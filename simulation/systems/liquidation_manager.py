from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from simulation.firms import Firm
    from simulation.finance.api import ISettlementSystem
    from simulation.dtos.api import SimulationState

logger = logging.getLogger(__name__)

@dataclass
class Claim:
    """Represents a creditor's claim against the firm."""
    creditor_id: Any
    amount: float
    tier: int
    description: str

class LiquidationManager:
    """
    Manages the liquidation waterfall process for insolvent firms.
    Implements TD-187 Protocol.
    """

    def __init__(self, settlement_system: ISettlementSystem):
        self.settlement_system = settlement_system

    def initiate_liquidation(self, firm: Firm, state: SimulationState) -> None:
        """
        Executes the liquidation waterfall.
        """
        if not hasattr(firm, 'finance'):
            logger.error(f"LIQUIDATION_ERROR | Firm {firm.id} missing finance component.")
            return

        current_tick = state.time
        available_cash = firm.finance.balance

        # 1. Calculate Claims
        claims = self.calculate_claims(firm, state)

        logger.info(
            f"LIQUIDATION_START | Firm {firm.id} starting liquidation. Assets: {available_cash:.2f}, Total Claims: {sum(c.amount for c in claims):.2f}",
            extra={"tick": current_tick, "agent_id": firm.id, "tags": ["liquidation", "waterfall"]}
        )

        # 2. Execute Waterfall
        self.execute_waterfall(firm, claims, available_cash, state)

    def calculate_claims(self, firm: Firm, state: SimulationState) -> List[Claim]:
        """
        Calculates all claims and assigns priority tiers.
        Tier 1: Employee Severance & Unpaid Wages
        Tier 2: Secured Creditors (Loans)
        Tier 3: Unsecured Priority (Taxes)
        Tier 4: General Unsecured
        Tier 5: Equity Holders
        """
        claims = []
        ticks_per_year = getattr(firm.config, "ticks_per_year", 365)

        # --- Tier 1: Employee Entitlements ---

        # A. Unpaid Wages (from HR tracking)
        # Cap at 3 months (ticks_per_year / 4)
        wage_cutoff_tick = state.time - (ticks_per_year // 4)

        if hasattr(firm.hr, 'unpaid_wages'):
            for employee_id, wage_records in firm.hr.unpaid_wages.items():
                # Filter strict 3-month window
                total_unpaid = sum(amount for tick, amount in wage_records if tick >= wage_cutoff_tick)
                if total_unpaid > 0:
                    claims.append(Claim(
                        creditor_id=employee_id,
                        amount=total_unpaid,
                        tier=1,
                        description="Unpaid Wages"
                    ))

        # B. Severance Pay
        # "Accrued severance pay for all employees over the last 3 years of service."

        accrual_rate_weeks = getattr(firm.config, "severance_pay_weeks", 2.0)
        current_tick = state.time
        ticks_per_week = ticks_per_year / 52.0

        for employee in firm.hr.employees:
            # Calculate Tenure
            start_tick = getattr(employee._econ_state, 'employment_start_tick', -1)
            tenure_years = 0.0
            if start_tick >= 0:
                tenure_years = (current_tick - start_tick) / ticks_per_year

            # Cap at 3 years
            effective_tenure = min(tenure_years, 3.0)

            # Calculate Severance Amount
            current_wage = firm.hr.employee_wages.get(employee.id, 0.0)
            if current_wage > 0:
                # Formula: Years * Weeks/Year * Ticks/Week * Wage/Tick
                severance_ticks = effective_tenure * accrual_rate_weeks * ticks_per_week
                severance_amount = severance_ticks * current_wage

                if severance_amount > 0:
                    claims.append(Claim(
                        creditor_id=employee.id,
                        amount=severance_amount,
                        tier=1,
                        description=f"Severance ({effective_tenure:.2f} yr)"
                    ))

        # --- Tier 2: Secured Creditors (Bank Loans) ---
        # Query bank if possible
        total_debt = getattr(firm, 'total_debt', 0.0)
        # Attempt to get exact creditor (Bank)
        bank_agent = None
        if hasattr(firm, 'decision_engine') and hasattr(firm.decision_engine, 'loan_market'):
            loan_market = firm.decision_engine.loan_market
            if loan_market and hasattr(loan_market, 'bank') and loan_market.bank:
                bank_agent = loan_market.bank

        if total_debt > 0:
            claims.append(Claim(
                creditor_id=bank_agent.id if bank_agent else "BANK_UNKNOWN",
                amount=total_debt,
                tier=2,
                description="Secured Loan"
            ))

        # --- Tier 3: Unsecured Priority (Taxes) ---
        # We assume current tick's tax liability if profit exists, plus any potential unpaid backlog (not tracked currently).
        # We'll rely on what FinanceDepartment would have paid.
        # But FinanceDepartment calcs tax on *paid* revenue? Or accrued?
        # `generate_tax_transaction` uses `revenue_this_turn`.
        # If we are liquidating, we might have revenue from inventory liquidation (if we sold it).
        # But here we are distributing CASH.
        # Let's estimate tax on `retained_earnings` if that's a proxy for untaxed profit?
        # Or better: `current_profit` * `corporate_tax_rate`.

        tax_rate = getattr(firm.config, "corporate_tax_rate", 0.0)
        if firm.finance.current_profit > 0:
            tax_liability = firm.finance.current_profit * tax_rate

            # Find Government ID
            # Usually passed in methods, but we need to find it.
            # Using 'system' or looking up via settlement system if possible?
            # Or pass it in? `initiate_liquidation` doesn't take gov.
            # We can use a string placeholder if ID unknown, but SettlementSystem needs valid ID.
            # We will try to find "government" in firm's known agents or similar.
            # But usually tax is paid to ID 0 or "government".
            # Let's assume there is a government agent.
            # Workaround: Use string "government" if ID not found, but SettlementSystem might fail.
            # Better: `LiquidationManager` should ideally have access to registry.
            # But for now, let's leave creditor_id as "government" and handle resolution in execute.

            claims.append(Claim(
                creditor_id="government",
                amount=tax_liability,
                tier=3,
                description="Corporate Tax"
            ))

        # --- Tier 5: Equity Holders (Shareholders) ---
        # We don't add them as fixed claims because they are residual.
        # But to be consistent with "Waterfall", we can add them as claims equal to their share % * remaining.
        # But the standard way is: Claims are fixed. Equity gets *everything else*.
        # So we won't add them to the list of fixed claims. We handle them as the "Residual" tier in execution.

        return claims

    def execute_waterfall(self, firm: Firm, claims: List[Claim], available_cash: float, state: SimulationState) -> None:
        """
        Distributes cash according to tiers.
        """
        current_tick = state.time
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
                    self._pay_claim(firm, claim, claim.amount, state)
                remaining_cash -= total_tier_claim
                logger.info(f"LIQUIDATION_WATERFALL | Tier {tier} fully paid. Remaining cash: {remaining_cash:.2f}")
            else:
                # Pay pro-rata
                factor = remaining_cash / total_tier_claim
                for claim in tier_claims:
                    payment = claim.amount * factor
                    self._pay_claim(firm, claim, payment, state, partial=True)
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
                        self.settlement_system.transfer(firm, agent, distribution, "Liquidation Dividend (Tier 5)")
                        total_distributed += distribution

                logger.info(f"LIQUIDATION_WATERFALL | Tier 5 (Equity) distributed {total_distributed:.2f} to shareholders.")

    def _pay_claim(self, firm: Firm, claim: Claim, amount: float, state: SimulationState, partial: bool = False):
        """Helper to execute transfer."""
        if amount <= 0:
            return

        creditor_id = claim.creditor_id
        creditor = None

        # Resolve Creditor Object
        if creditor_id == "government":
            if hasattr(state, "government"):
                creditor = state.government
        elif creditor_id in state.agents:
            creditor = state.agents[creditor_id]
        else:
             # Try households list if not in main agents map (though it should be)
             # or look in other lists
             pass

        if creditor:
            memo = f"Liquidation Payout: {claim.description}" + (" (Partial)" if partial else "")
            success = self.settlement_system.transfer(firm, creditor, amount, memo)
            if not success:
                 logger.error(f"LIQUIDATION_PAYMENT_FAIL | Failed to transfer {amount:.2f} to {creditor.id}")
        else:
            logger.warning(f"LIQUIDATION_PAYMENT_SKIP | Creditor {creditor_id} not found for claim {claim.description}")
