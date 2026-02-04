from __future__ import annotations
from typing import List, TYPE_CHECKING, Optional, Any
import logging
from modules.common.dtos import Claim
from modules.system.api import DEFAULT_CURRENCY
from simulation.systems.liquidation_handlers import InventoryLiquidationHandler, ILiquidationHandler

if TYPE_CHECKING:
    from simulation.firms import Firm
    from simulation.finance.api import ISettlementSystem
    from simulation.dtos.api import SimulationState
    from modules.system.api import IAssetRecoverySystem, IAgentRegistry
    from modules.hr.api import IHRService
    from modules.finance.api import ITaxService

logger = logging.getLogger(__name__)

class LiquidationManager:
    """
    Manages the liquidation waterfall process for insolvent firms.
    Implements TD-187 Protocol.
    Refactored to comply with SRP (WO-211).
    """

    def __init__(self,
                 settlement_system: ISettlementSystem,
                 hr_service: IHRService,
                 tax_service: ITaxService,
                 agent_registry: IAgentRegistry,
                 public_manager: Optional[IAssetRecoverySystem] = None):
        self.settlement_system = settlement_system
        self.hr_service = hr_service
        self.tax_service = tax_service
        self.agent_registry = agent_registry
        self.public_manager = public_manager

        self.handlers: List[ILiquidationHandler] = []
        if self.public_manager:
            self.handlers.append(InventoryLiquidationHandler(self.settlement_system, self.public_manager))

    def initiate_liquidation(self, firm: Firm, state: SimulationState) -> None:
        """
        Executes the liquidation waterfall.
        """
        if not hasattr(firm, 'finance'):
            logger.error(f"LIQUIDATION_ERROR | Firm {firm.id} missing finance component.")
            return

        current_tick = state.time

        # 0. Asset Liquidation (TD-187-LEAK Fix)
        # Use registered handlers to liquidate assets.
        for handler in self.handlers:
            handler.liquidate(firm, state)

        # Re-fetch cash after liquidation
        available_cash_raw = firm.finance.balance
        available_cash = available_cash_raw
        if isinstance(available_cash_raw, dict):
            available_cash = available_cash_raw.get(DEFAULT_CURRENCY, 0.0)

        all_claims: List[Claim] = []

        # 1. Get HR Claims (Tier 1)
        employee_claims = self.hr_service.calculate_liquidation_employee_claims(firm, current_tick)
        all_claims.extend(employee_claims)

        # 2. Get Tax Claims (Tier 3)
        tax_claims = self.tax_service.calculate_liquidation_tax_claims(firm)
        all_claims.extend(tax_claims)

        # 3. Get Secured Debt Claims (Tier 2)
        # Query firm.finance for secured debt (e.g., bank loans).
        total_debt = getattr(firm, 'total_debt', 0.0)
        bank_agent = None
        if hasattr(firm, 'decision_engine') and hasattr(firm.decision_engine, 'loan_market'):
            loan_market = firm.decision_engine.loan_market
            if loan_market and hasattr(loan_market, 'bank') and loan_market.bank:
                bank_agent = loan_market.bank

        if total_debt > 0:
            all_claims.append(Claim(
                creditor_id=bank_agent.id if bank_agent else "BANK_UNKNOWN",
                amount=total_debt,
                tier=2,
                description="Secured Loan"
            ))

        logger.info(
            f"LIQUIDATION_START | Firm {firm.id} starting liquidation. Assets: {available_cash:.2f}, Total Claims: {sum(c.amount for c in all_claims):.2f}",
            extra={"tick": current_tick, "agent_id": firm.id, "tags": ["liquidation", "waterfall"]}
        )

        # 4. Execute Waterfall
        self.execute_waterfall(firm, all_claims, available_cash, state)

    def execute_waterfall(self, firm: Firm, claims: List[Claim], available_cash: float, state: SimulationState) -> None:
        """
        Distributes cash according to tiers.
        """
        remaining_cash = available_cash

        # Sort claims by tier
        claims.sort(key=lambda c: c.tier)

        # Group by tier
        claims_by_tier = {}
        for c in claims:
            if c.tier not in claims_by_tier:
                claims_by_tier[c.tier] = []
            claims_by_tier[c.tier].append(c)

        # Iterate tiers 1 to 4
        for tier in range(1, 5):
            if tier not in claims_by_tier:
                continue

            tier_claims = claims_by_tier[tier]
            total_tier_claim = sum(c.amount for c in tier_claims)

            if remaining_cash <= 0:
                logger.info(f"LIQUIDATION_WATERFALL | Tier {tier} reached with 0 cash. Claims unpaid: {total_tier_claim:.2f}")
                break

            if remaining_cash >= total_tier_claim:
                # Pay all fully
                for claim in tier_claims:
                    self._pay_claim(firm, claim, claim.amount)
                remaining_cash -= total_tier_claim
                logger.info(f"LIQUIDATION_WATERFALL | Tier {tier} fully paid. Remaining cash: {remaining_cash:.2f}")
            else:
                # Pay pro-rata
                factor = remaining_cash / total_tier_claim
                for claim in tier_claims:
                    payment = claim.amount * factor
                    self._pay_claim(firm, claim, payment, partial=True)
                remaining_cash = 0.0
                logger.info(f"LIQUIDATION_WATERFALL | Tier {tier} partially paid (Factor: {factor:.2f}). Cash exhausted.")

        # --- Tier 5: Equity ---
        if remaining_cash > 0:
            outstanding_shares = firm.total_shares - firm.treasury_shares
            if outstanding_shares > 0:
                # Gather shareholders from state
                shareholders = list(state.households)
                if hasattr(state, 'government') and state.government:
                    shareholders.append(state.government)

                total_distributed = 0.0
                for agent in shareholders:
                    shares = 0
                    if hasattr(agent, "shares_owned"):
                        shares = agent.shares_owned.get(firm.id, 0)

                    if shares > 0:
                        share_ratio = shares / outstanding_shares
                        distribution = remaining_cash * share_ratio
                        self.settlement_system.transfer(firm, agent, distribution, "Liquidation Dividend (Tier 5)", currency=DEFAULT_CURRENCY)
                        total_distributed += distribution

                logger.info(f"LIQUIDATION_WATERFALL | Tier 5 (Equity) distributed {total_distributed:.2f} to shareholders.")

    def _pay_claim(self, firm: Firm, claim: Claim, amount: float, partial: bool = False):
        """Helper to execute transfer using AgentRegistry."""
        if amount <= 0:
            return

        creditor_id = claim.creditor_id
        creditor = self.agent_registry.get_agent(creditor_id)

        if creditor:
            memo = f"Liquidation Payout: {claim.description}" + (" (Partial)" if partial else "")
            success = self.settlement_system.transfer(firm, creditor, amount, memo, currency=DEFAULT_CURRENCY)
            if not success:
                 logger.error(f"LIQUIDATION_PAYMENT_FAIL | Failed to transfer {amount:.2f} to {creditor.id}")
        else:
            logger.warning(f"LIQUIDATION_PAYMENT_SKIP | Creditor {creditor_id} not found for claim {claim.description}")
