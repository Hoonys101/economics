from typing import List, Any
import logging
from modules.government.engines.api import (
    IFiscalEngine,
    FiscalStateDTO,
    FiscalRequestDTO,
    FiscalDecisionDTO,
    GrantedBailoutDTO
)
from modules.system.api import MarketSnapshotDTO, CurrencyCode, DEFAULT_CURRENCY

logger = logging.getLogger(__name__)

DEBT_CEILING_RATIO = 1.5
AUSTERITY_TRIGGER_RATIO = 1.0

class FiscalEngine(IFiscalEngine):
    """
    Stateless engine that decides on government fiscal policy actions.
    Implements Taylor Rule for tax adjustments and evaluates bailout requests.
    Enforces Solvency Guardrails (Debt Brake, Bailout Limits).
    """

    def __init__(self, config_module: Any = None):
        self.config = config_module

    def decide(
        self,
        state: FiscalStateDTO,
        market: MarketSnapshotDTO,
        requests: List[FiscalRequestDTO]
    ) -> FiscalDecisionDTO:

        # 1. Calculate Fiscal Stance (Tax Rates)
        new_income_tax_rate, new_corporate_tax_rate, fiscal_stance = self._calculate_tax_rates(state, market)

        # 2. Calculate Welfare Multiplier (Debt Brake)
        new_welfare_budget_multiplier = self._calculate_welfare_multiplier(state)

        # 3. Evaluate Bailout Requests
        bailouts_to_grant = self._evaluate_bailouts(requests, state)

        # 4. Construct Decision
        decision = FiscalDecisionDTO(
            new_income_tax_rate=new_income_tax_rate,
            new_corporate_tax_rate=new_corporate_tax_rate,
            new_welfare_budget_multiplier=new_welfare_budget_multiplier,
            bailouts_to_grant=bailouts_to_grant
        )

        return decision

    def _calculate_tax_rates(self, state: FiscalStateDTO, market: MarketSnapshotDTO):
        # Access current_gdp from market_data (safe access with default)
        current_gdp = market.market_data.get("current_gdp", 0.0)
        potential_gdp = state.potential_gdp

        # Debt check
        total_debt = state.total_debt
        debt_to_gdp = 0.0
        if potential_gdp > 0:
            debt_to_gdp = total_debt / potential_gdp
        elif current_gdp > 0:
             debt_to_gdp = total_debt / current_gdp

        # Default fallback
        new_income_tax_rate = state.income_tax_rate
        new_corporate_tax_rate = state.corporate_tax_rate
        fiscal_stance = 0.0

        if potential_gdp > 0:
            gdp_gap = (current_gdp - potential_gdp) / potential_gdp

            # Counter-Cyclical Logic
            auto_cyclical = getattr(self.config, "AUTO_COUNTER_CYCLICAL_ENABLED", True)

            if auto_cyclical:
                sensitivity = getattr(self.config, "FISCAL_SENSITIVITY_ALPHA", 0.5)
                base_income_tax = getattr(self.config, "INCOME_TAX_RATE", 0.1)
                base_corp_tax = getattr(self.config, "CORPORATE_TAX_RATE", 0.2)

                fiscal_stance = -sensitivity * gdp_gap

                # Adjust Income Tax
                # If stance > 0 (Expansionary), lower tax.
                # If stance < 0 (Contractionary), raise tax.
                # Formula: rate = base * (1 - stance)
                new_income_tax_rate = base_income_tax * (1.0 - fiscal_stance)
                new_corporate_tax_rate = base_corp_tax * (1.0 - fiscal_stance)

                # Clamp values
                new_income_tax_rate = max(0.05, min(0.6, new_income_tax_rate))
                new_corporate_tax_rate = max(0.05, min(0.6, new_corporate_tax_rate))

        # --- DEBT BRAKE OVERRIDE ---
        # If debt is too high, force tax hikes (or prevent cuts) regardless of recession
        if debt_to_gdp > DEBT_CEILING_RATIO:
            # Force rate towards higher end or at least base rate + penalty
            base_income_tax = getattr(self.config, "INCOME_TAX_RATE", 0.1)
            base_corp_tax = getattr(self.config, "CORPORATE_TAX_RATE", 0.2)

            # Simple logic: Ensure rates are at least base, and add surcharge
            new_income_tax_rate = max(new_income_tax_rate, base_income_tax * 1.1)
            new_corporate_tax_rate = max(new_corporate_tax_rate, base_corp_tax * 1.1)

            # Ensure we don't go crazy
            new_income_tax_rate = min(0.6, new_income_tax_rate)
            new_corporate_tax_rate = min(0.6, new_corporate_tax_rate)

        return new_income_tax_rate, new_corporate_tax_rate, fiscal_stance

    def _calculate_welfare_multiplier(self, state: FiscalStateDTO) -> float:
        total_debt = state.total_debt
        potential_gdp = state.potential_gdp

        if potential_gdp <= 0:
            return 1.0

        debt_to_gdp = total_debt / potential_gdp

        if debt_to_gdp > DEBT_CEILING_RATIO:
            # Drastic Cut
            return 0.5
        elif debt_to_gdp > AUSTERITY_TRIGGER_RATIO:
            # Linear reduction from 1.0 to 0.5 as debt goes from 1.0 to 1.5
            # Formula: 1.0 - (ratio - 1.0)
            # if ratio = 1.0 -> 1.0
            # if ratio = 1.5 -> 0.5
            return max(0.5, 1.0 - (debt_to_gdp - AUSTERITY_TRIGGER_RATIO))

        return 1.0

    def _evaluate_bailouts(self, requests: List[FiscalRequestDTO], state: FiscalStateDTO) -> List[GrantedBailoutDTO]:
        total_debt = state.total_debt
        potential_gdp = state.potential_gdp
        current_assets = state.assets.get(DEFAULT_CURRENCY, 0)

        debt_to_gdp = 0.0
        if potential_gdp > 0:
            debt_to_gdp = total_debt / potential_gdp

        # Reject all if Debt Ceiling breached
        if debt_to_gdp > DEBT_CEILING_RATIO:
            return []

        granted = []
        for req in requests:
            if req.bailout_request:
                bailout_req = req.bailout_request
                amount = bailout_req.requested_amount

                # Check 1: Can we afford it liquidly?
                # Ideally we check bond capacity too, but "Solvency Guardrails" implies prudence.
                # If we have cash, use it. If not, can we issue bond?
                # If debt is low (< 1.0), we assume we can issue bond.
                # If debt is moderate (1.0 - 1.5), we require cash on hand.

                can_afford = False
                if current_assets >= amount:
                    can_afford = True
                elif debt_to_gdp < AUSTERITY_TRIGGER_RATIO:
                    can_afford = True # Assume bond market access

                if not can_afford:
                    continue

                financials = bailout_req.firm_financials
                is_solvent = financials.is_solvent

                if is_solvent:
                    # Grant bailout
                    granted.append(GrantedBailoutDTO(
                        firm_id=bailout_req.firm_id,
                        amount=amount, # Integer
                        interest_rate=0.05, # Default term
                        term=50 # Default term ticks
                    ))
        return granted
