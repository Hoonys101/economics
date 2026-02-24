from typing import List, Any, Union, Optional
import logging
from modules.government.engines.api import (
    IFiscalEngine,
    FiscalStateDTO,
    FiscalRequestDTO,
    FiscalDecisionDTO,
    GrantedBailoutDTO,
    FiscalConfigDTO,
    FirmBailoutRequestDTO
)
from modules.system.api import MarketSnapshotDTO, CurrencyCode, DEFAULT_CURRENCY

logger = logging.getLogger(__name__)

class FiscalEngine(IFiscalEngine):
    """
    Stateless engine that decides on government fiscal policy actions.
    Implements Taylor Rule for tax adjustments and evaluates bailout requests.
    Enforces Solvency Guardrails (Debt Brake, Bailout Limits).
    """

    def __init__(self, config_module: FiscalConfigDTO):
        # We enforce FiscalConfigDTO. If Any is passed, it must behave like the DTO or we might fail.
        # Ideally we'd check isinstance, but for now we trust the type hint.
        self.config_dto = config_module

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
        # Assuming market_data is a dict or object.
        # MarketSnapshotDTO usually has market_data as dict?
        market_data = getattr(market, 'market_data', {})
        current_gdp = 0.0
        if isinstance(market_data, dict):
             current_gdp = market_data.get("current_gdp", 0.0)
        else:
             # Fallback if it's an object
             current_gdp = getattr(market_data, "current_gdp", 0.0)

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

        # Config Access (Strict DTO)
        tax_min = self.config_dto.tax_rate_min
        tax_max = self.config_dto.tax_rate_max
        debt_ceiling = self.config_dto.debt_ceiling_ratio

        # New constant: Hard Limit (Direct Access)
        debt_hard_limit = self.config_dto.debt_ceiling_hard_limit_ratio

        if potential_gdp > 0:
            gdp_gap = (current_gdp - potential_gdp) / potential_gdp

            # Counter-Cyclical Logic
            auto_cyclical = self.config_dto.auto_counter_cyclical_enabled

            if auto_cyclical:
                sensitivity = self.config_dto.fiscal_sensitivity_alpha
                base_income_tax = self.config_dto.base_income_tax_rate
                base_corp_tax = self.config_dto.base_corporate_tax_rate

                fiscal_stance = -sensitivity * gdp_gap

                # Adjust Income Tax
                # If stance > 0 (Expansionary), lower tax.
                # If stance < 0 (Contractionary), raise tax.
                # Formula: rate = base * (1 - stance)
                new_income_tax_rate = base_income_tax * (1.0 - fiscal_stance)
                new_corporate_tax_rate = base_corp_tax * (1.0 - fiscal_stance)

                # Clamp values
                new_income_tax_rate = max(tax_min, min(tax_max, new_income_tax_rate))
                new_corporate_tax_rate = max(tax_min, min(tax_max, new_corporate_tax_rate))

        # --- DEBT BRAKE OVERRIDE ---
        # If debt is too high, force tax hikes (or prevent cuts) regardless of recession
        # Use Hard Limit if available, else standard ceiling?
        # Standard logic: if debt > ceiling, force higher rates.
        effective_ceiling = debt_hard_limit if debt_hard_limit > 0 else debt_ceiling

        if debt_to_gdp > effective_ceiling:
            # Force rate towards higher end or at least base rate + penalty
            base_income_tax = self.config_dto.base_income_tax_rate
            base_corp_tax = self.config_dto.base_corporate_tax_rate

            # Simple logic: Ensure rates are at least base, and add surcharge
            new_income_tax_rate = max(new_income_tax_rate, base_income_tax * 1.1)
            new_corporate_tax_rate = max(new_corporate_tax_rate, base_corp_tax * 1.1)

            # Ensure we don't go crazy
            new_income_tax_rate = min(tax_max, new_income_tax_rate)
            new_corporate_tax_rate = min(tax_max, new_corporate_tax_rate)

        return new_income_tax_rate, new_corporate_tax_rate, fiscal_stance

    def _calculate_welfare_multiplier(self, state: FiscalStateDTO) -> float:
        total_debt = state.total_debt
        potential_gdp = state.potential_gdp

        debt_ceiling = self.config_dto.debt_ceiling_ratio
        austerity_trigger = self.config_dto.austerity_trigger_ratio

        if potential_gdp <= 0:
            return 1.0

        debt_to_gdp = total_debt / potential_gdp

        if debt_to_gdp > debt_ceiling:
            # Drastic Cut
            return 0.5
        elif debt_to_gdp > austerity_trigger:
            # Linear reduction from 1.0 to 0.5 as debt goes from 1.0 to 1.5
            # Formula: 1.0 - (ratio - 1.0)
            # if ratio = 1.0 -> 1.0
            # if ratio = 1.5 -> 0.5
            return max(0.5, 1.0 - (debt_to_gdp - austerity_trigger))

        return 1.0

    def _evaluate_bailouts(self, requests: List[FiscalRequestDTO], state: FiscalStateDTO) -> List[GrantedBailoutDTO]:
        total_debt = state.total_debt
        potential_gdp = state.potential_gdp
        current_assets = state.assets.get(DEFAULT_CURRENCY, 0)

        debt_ceiling = self.config_dto.debt_ceiling_ratio
        austerity_trigger = self.config_dto.austerity_trigger_ratio

        debt_to_gdp = 0.0
        if potential_gdp > 0:
            debt_to_gdp = total_debt / potential_gdp

        # Reject all if Debt Ceiling breached
        if debt_to_gdp > debt_ceiling:
            return []

        granted = []
        for req in requests:
            if req.bailout_request:
                bailout_req = req.bailout_request
                amount = bailout_req.requested_amount

                # Check 1: Can we afford it liquidly?
                can_afford = False
                if current_assets >= amount:
                    can_afford = True
                elif debt_to_gdp < austerity_trigger:
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
