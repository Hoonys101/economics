from __future__ import annotations
from typing import List, TYPE_CHECKING, Optional, Any, Dict
import logging
from modules.common.financial.dtos import Claim
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode
from simulation.systems.liquidation_handlers import InventoryLiquidationHandler, ILiquidationHandler
from modules.finance.api import ILiquidatable, LiquidationContext

if TYPE_CHECKING:
    from simulation.firms import Firm
    from simulation.finance.api import ISettlementSystem
    from simulation.dtos.api import SimulationState
    from modules.system.api import IAssetRecoverySystem, IAgentRegistry
    from modules.hr.api import IHRService
    from modules.finance.api import ITaxService, IShareholderRegistry

logger = logging.getLogger(__name__)

class LiquidationManager:
    """
    Manages the liquidation waterfall process for insolvent firms.
    Implements TD-187 Protocol.
    Refactored to comply with SRP (WO-211) and TD-269 Protocol Purity.
    """

    def __init__(self,
                 settlement_system: ISettlementSystem,
                 hr_service: IHRService,
                 tax_service: ITaxService,
                 agent_registry: IAgentRegistry,
                 shareholder_registry: IShareholderRegistry,
                 public_manager: Optional[IAssetRecoverySystem] = None):
        self.settlement_system = settlement_system
        self.hr_service = hr_service
        self.tax_service = tax_service
        self.agent_registry = agent_registry
        self.shareholder_registry = shareholder_registry
        self.public_manager = public_manager

        self.handlers: List[ILiquidationHandler] = []
        if self.public_manager:
            self.handlers.append(InventoryLiquidationHandler(self.settlement_system, self.public_manager))

    def initiate_liquidation(self, agent: ILiquidatable, state: SimulationState) -> None:
        """
        Executes the liquidation waterfall.
        Refactored to use ILiquidatable protocol (TD-269).
        """
        if not isinstance(agent, ILiquidatable):
            logger.error(f"LIQUIDATION_ERROR | Agent {agent.id} does not implement ILiquidatable.")
            return

        current_tick = state.time

        # 0. Asset Liquidation (TD-187-LEAK Fix)
        # Use registered handlers to liquidate assets (Sell-offs).
        for handler in self.handlers:
            handler.liquidate(agent, state)

        # 1. Firm Write-offs (WO-212 Atomicity)
        # Write off remaining assets (Inventory, Capital Stock) and finalize bankruptcy.
        # Returns the final cash balance for distribution.
        all_assets_dict = agent.liquidate_assets(state.time)

        # TD-033: Handle Multi-Currency
        available_cash = all_assets_dict.get(DEFAULT_CURRENCY, 0)
        other_assets = {k: v for k, v in all_assets_dict.items() if k != DEFAULT_CURRENCY and v > 0}

        # 2. Build Liquidation Context
        context = LiquidationContext(
            current_tick=state.time,
            hr_service=self.hr_service,
            tax_service=self.tax_service,
            shareholder_registry=self.shareholder_registry
        )

        # 3. Get all claims via the protocol
        all_claims = agent.get_all_claims(context)

        logger.info(
            f"LIQUIDATION_START | Agent {agent.id} starting liquidation. Assets: {available_cash}, Total Claims: {sum(c.amount_pennies for c in all_claims)}",
            extra={"tick": current_tick, "agent_id": agent.id, "tags": ["liquidation", "waterfall"]}
        )

        # 4. Execute Waterfall
        self.execute_waterfall(agent, all_claims, available_cash, state, other_assets)

    def execute_waterfall(self, agent: ILiquidatable, claims: List[Claim], available_cash: float, state: SimulationState, other_assets: Dict[CurrencyCode, float] = None) -> None:
        """
        Distributes cash according to tiers.
        TD-033: Added other_assets for Tier 5 distribution.
        """
        if other_assets is None:
            other_assets = {}

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
            total_tier_claim = sum(c.amount_pennies for c in tier_claims)

            if remaining_cash <= 0:
                logger.info(f"LIQUIDATION_WATERFALL | Tier {tier} reached with 0 cash. Claims unpaid: {total_tier_claim}")
                break

            if remaining_cash >= total_tier_claim:
                # Pay all fully
                for claim in tier_claims:
                    self._pay_claim(agent, claim, claim.amount_pennies)
                remaining_cash -= total_tier_claim
                logger.info(f"LIQUIDATION_WATERFALL | Tier {tier} fully paid. Remaining cash: {remaining_cash}")
            else:
                # Pay pro-rata
                factor = remaining_cash / total_tier_claim
                for claim in tier_claims:
                    payment = int(claim.amount_pennies * factor)
                    self._pay_claim(agent, claim, payment, partial=True)
                remaining_cash = 0.0
                logger.info(f"LIQUIDATION_WATERFALL | Tier {tier} partially paid (Factor: {factor:.2f}). Cash exhausted.")

        # --- Tier 5: Equity ---
        # TD-033: Check if there is ANY value to distribute (Cash or Foreign Assets)
        if remaining_cash > 0 or other_assets:
            # Get equity stakes via protocol, not global state
            context = LiquidationContext(current_tick=state.time, shareholder_registry=self.shareholder_registry)
            equity_stakes = agent.get_equity_stakes(context)

            if equity_stakes:
                total_distributed_cash = 0.0
                total_distributed_foreign = {}

                for stake in equity_stakes:
                    shareholder = self.agent_registry.get_agent(stake.shareholder_id)
                    ratio = stake.ratio

                    if shareholder and ratio > 0:
                        # 1. Distribute Primary Currency
                        if remaining_cash > 0:
                            distribution = remaining_cash * ratio
                            self.settlement_system.transfer(agent, shareholder, distribution, "Liquidation Dividend (Tier 5)", currency=DEFAULT_CURRENCY)
                            total_distributed_cash += distribution

                        # 2. Distribute Foreign Currencies (TD-033)
                        for cur, amount in other_assets.items():
                            if amount > 0:
                                dist_amount = amount * ratio
                                self.settlement_system.transfer(agent, shareholder, dist_amount, f"Liquidation Dividend (Tier 5 - {cur})", currency=cur)
                                total_distributed_foreign[cur] = total_distributed_foreign.get(cur, 0.0) + dist_amount

                logger.info(f"LIQUIDATION_WATERFALL | Tier 5 (Equity) distributed {total_distributed_cash:.2f} {DEFAULT_CURRENCY} and foreign assets: {total_distributed_foreign} to shareholders.")

    def _pay_claim(self, agent: ILiquidatable, claim: Claim, amount_pennies: int, partial: bool = False):
        """Helper to execute transfer using AgentRegistry."""
        if amount_pennies <= 0:
            return

        creditor_id = claim.creditor_id
        creditor = self.agent_registry.get_agent(creditor_id)

        if creditor:
            memo = f"Liquidation Payout: {claim.description}" + (" (Partial)" if partial else "")
            success = self.settlement_system.transfer(agent, creditor, amount_pennies, memo, currency=DEFAULT_CURRENCY)

            if success:
                # Phase 4.1: If creditor is a Bank, apply generic repayment to update ledger
                if hasattr(creditor, 'receive_repayment'):
                    creditor.receive_repayment(agent.id, amount_pennies)

            if not success:
                 logger.error(f"LIQUIDATION_PAYMENT_FAIL | Failed to transfer {amount_pennies} to {creditor.id}")
        else:
            logger.warning(f"LIQUIDATION_PAYMENT_SKIP | Creditor {creditor_id} not found for claim {claim.description}")
