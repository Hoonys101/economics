from typing import List, Any
import logging
from modules.government.engines.api import (
    IFiscalEngine,
    FiscalStateDTO,
    FiscalRequestDTO,
    FiscalDecisionDTO,
    GrantedBailoutDTO
)
from modules.system.api import MarketSnapshotDTO, CurrencyCode

logger = logging.getLogger(__name__)

class FiscalEngine(IFiscalEngine):
    """
    Stateless engine that decides on government fiscal policy actions.
    Implements Taylor Rule for tax adjustments and evaluates bailout requests.
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

        # 2. Evaluate Bailout Requests
        bailouts_to_grant = self._evaluate_bailouts(requests)

        # 3. Construct Decision
        decision = FiscalDecisionDTO(
            new_income_tax_rate=new_income_tax_rate,
            new_corporate_tax_rate=new_corporate_tax_rate,
            new_welfare_budget_multiplier=state["welfare_budget_multiplier"],
            bailouts_to_grant=bailouts_to_grant
        )

        return decision

    def _calculate_tax_rates(self, state: FiscalStateDTO, market: MarketSnapshotDTO):
        # Access current_gdp from market_data (safe access with default)
        current_gdp = market.market_data.get("current_gdp", 0.0)
        potential_gdp = state["potential_gdp"]

        # Default fallback
        new_income_tax_rate = state["income_tax_rate"]
        new_corporate_tax_rate = state["corporate_tax_rate"]
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

        return new_income_tax_rate, new_corporate_tax_rate, fiscal_stance

    def _evaluate_bailouts(self, requests: List[FiscalRequestDTO]) -> List[GrantedBailoutDTO]:
        granted = []
        for req in requests:
            if req.get("bailout_request"):
                bailout_req = req["bailout_request"]

                financials = bailout_req["firm_financials"]
                is_solvent = financials["is_solvent"]

                if is_solvent:
                    # Grant bailout
                    granted.append(GrantedBailoutDTO(
                        firm_id=bailout_req["firm_id"],
                        amount=bailout_req["requested_amount"],
                        interest_rate=0.05, # Default term
                        term=50 # Default term ticks
                    ))
        return granted
