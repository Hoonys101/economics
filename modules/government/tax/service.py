from typing import Any, Dict, Optional, List
from decimal import Decimal
from modules.government.api import ITaxService
from modules.government.taxation.system import TaxationSystem
from modules.government.components.fiscal_policy_manager import FiscalPolicyManager
from modules.government.dtos import (
    FiscalPolicyDTO,
    TaxCollectionResultDTO,
    PaymentRequestDTO,
    IAgent
)
from modules.finance.api import TaxCollectionResult
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY
from simulation.dtos.api import MarketSnapshotDTO
from modules.government.constants import (
    DEFAULT_ANNUAL_WEALTH_TAX_RATE,
    DEFAULT_WEALTH_TAX_THRESHOLD,
    DEFAULT_TICKS_PER_YEAR
)
from modules.finance.utils.currency_math import round_to_pennies

class TaxService(ITaxService):
    """
    Implementation of the ITaxService.
    Encapsulates tax calculation and revenue recording logic.
    MIGRATION: Uses integer pennies.
    """

    def __init__(self, config_module: Any):
        self.config_module = config_module

        # Composition of existing logic components
        self.taxation_system = TaxationSystem(config_module)
        self.fiscal_policy_manager = FiscalPolicyManager(config_module)

        # State initialization (extracted from Government agent)
        self.total_collected_tax: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: 0}
        self.revenue_this_tick: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: 0}
        self.tax_revenue: Dict[str, int] = {}

        # Detailed stats for the current tick
        self.current_tick_stats: Dict[str, Any] = {
            "tax_revenue": {},
            "total_collected": 0
        }

    def determine_fiscal_stance(self, snapshot: MarketSnapshotDTO) -> FiscalPolicyDTO:
        """Determines the current fiscal policy based on market conditions."""
        return self.fiscal_policy_manager.determine_fiscal_stance(snapshot)

    def calculate_tax_liability(self, policy: FiscalPolicyDTO, income: float) -> int:
        """Calculates the tax amount for a given income and fiscal policy."""
        # Income is likely float from legacy or int pennies from new system.
        # Policy rate is float.
        # Assume income is float dollars for now if coming from legacy?
        # No, if we are in the new world, income should be pennies.
        # But `Household.calculate_income_tax` passes `income` which is `labor_income_this_tick` (now int pennies).
        # So income is pennies.

        # Legacy manager might return float dollars. We need to handle this.
        # If `FiscalPolicyManager` is untouched, it just does `income * rate`.
        # int * float = float.
        # We just round it.
        raw_liability = self.fiscal_policy_manager.calculate_tax_liability(policy, income)
        return int(raw_liability) # round_to_pennies handles Decimal but here it's simple mul.

    def calculate_corporate_tax(self, profit: float, rate: float) -> int:
        """Calculates corporate tax based on profit and a flat rate."""
        # Profit is int pennies. Rate is float.
        raw = self.taxation_system.calculate_corporate_tax(profit, rate)
        return int(raw)

    def calculate_wealth_tax(self, net_worth: int) -> int:
        """Calculates wealth tax based on net worth (pennies)."""
        wealth_tax_rate_annual = getattr(self.config_module, "ANNUAL_WEALTH_TAX_RATE", DEFAULT_ANNUAL_WEALTH_TAX_RATE)
        ticks_per_year = getattr(self.config_module, "TICKS_PER_YEAR", DEFAULT_TICKS_PER_YEAR)

        if ticks_per_year <= 0:
             ticks_per_year = 100

        wealth_tax_rate_tick = wealth_tax_rate_annual / ticks_per_year
        # Threshold is likely in dollars in config. Convert to pennies.
        wealth_threshold_float = getattr(self.config_module, "WEALTH_TAX_THRESHOLD", DEFAULT_WEALTH_TAX_THRESHOLD)
        wealth_threshold = int(wealth_threshold_float * 100)

        if net_worth <= wealth_threshold:
            return 0

        tax_amount = round_to_pennies(Decimal(net_worth - wealth_threshold) * Decimal(wealth_tax_rate_tick))
        return max(0, min(tax_amount, net_worth))

    def collect_wealth_tax(self, agents: List[IAgent]) -> TaxCollectionResultDTO:
        """
        Calculates wealth tax for all eligible agents and returns a DTO
        containing payment requests for the government to execute.
        """
        requests = []
        total_projected = 0

        for agent in agents:
             if not getattr(agent, "is_active", False):
                 continue

             if hasattr(agent, "needs") and hasattr(agent, "is_employed"):
                net_worth = 0
                assets = getattr(agent, "assets", 0)
                if isinstance(assets, dict):
                     net_worth = int(assets.get(DEFAULT_CURRENCY, 0))
                else:
                     net_worth = int(assets)

                tax_amount = self.calculate_wealth_tax(net_worth)

                if tax_amount > 0:
                    requests.append(PaymentRequestDTO(
                        payer=agent,
                        payee="GOVERNMENT",
                        amount=tax_amount,
                        currency=DEFAULT_CURRENCY,
                        memo="wealth_tax"
                    ))
                    total_projected += tax_amount

        return TaxCollectionResultDTO(
            payment_requests=requests,
            total_collected=total_projected,
            tax_type="wealth_tax"
        )

    def record_revenue(self, result: TaxCollectionResult) -> None:
        """
        Updates internal ledgers based on a verified tax collection result.
        """
        if not result['success'] or result['amount_collected'] <= 0:
            return

        amount = int(result['amount_collected'])
        tax_type = result['tax_type']

        cur = result.get('currency', DEFAULT_CURRENCY)

        if cur not in self.total_collected_tax:
            self.total_collected_tax[cur] = 0
        if cur not in self.revenue_this_tick:
            self.revenue_this_tick[cur] = 0

        self.total_collected_tax[cur] += amount
        self.revenue_this_tick[cur] += amount

        self.tax_revenue[tax_type] = (
            self.tax_revenue.get(tax_type, 0) + amount
        )

        current_breakdown = self.current_tick_stats["tax_revenue"]
        current_breakdown[tax_type] = current_breakdown.get(tax_type, 0.0) + amount

        self.current_tick_stats["total_collected"] += amount

    def get_revenue_this_tick(self) -> Dict[CurrencyCode, int]:
        return self.revenue_this_tick.copy()

    def get_revenue_breakdown_this_tick(self) -> Dict[str, float]:
        return self.current_tick_stats["tax_revenue"].copy()

    def get_total_collected_this_tick(self) -> int:
        return int(self.current_tick_stats.get("total_collected", 0))

    def get_tax_revenue(self) -> Dict[str, int]:
        return self.tax_revenue.copy()

    def get_total_collected_tax(self) -> Dict[CurrencyCode, int]:
        return self.total_collected_tax.copy()

    def reset_tick_flow(self) -> None:
        self.revenue_this_tick = {DEFAULT_CURRENCY: 0}
        self.current_tick_stats = {
            "tax_revenue": {},
            "total_collected": 0
        }
