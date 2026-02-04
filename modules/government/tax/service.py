from typing import Any, Dict, Optional
from modules.government.tax.api import ITaxService
from modules.government.taxation.system import TaxationSystem
from modules.government.components.fiscal_policy_manager import FiscalPolicyManager
from modules.government.dtos import FiscalPolicyDTO
from modules.finance.api import TaxCollectionResult
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

class TaxService(ITaxService):
    """
    Implementation of the ITaxService.
    Encapsulates tax calculation and revenue recording logic.
    """

    def __init__(self, config_module: Any):
        self.config_module = config_module

        # Composition of existing logic components
        self.taxation_system = TaxationSystem(config_module)
        self.fiscal_policy_manager = FiscalPolicyManager(config_module)

        # State initialization (extracted from Government agent)
        self.total_collected_tax: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        self.revenue_this_tick: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        self.tax_revenue: Dict[str, float] = {}

        # Detailed stats for the current tick
        self.current_tick_stats: Dict[str, Any] = {
            "tax_revenue": {},
            "total_collected": 0.0
        }

    def calculate_tax_liability(self, policy: FiscalPolicyDTO, income: float) -> float:
        """Calculates the tax amount for a given income and fiscal policy."""
        return self.fiscal_policy_manager.calculate_tax_liability(policy, income)

    def calculate_corporate_tax(self, profit: float, rate: float) -> float:
        """Calculates corporate tax based on profit and a flat rate."""
        return self.taxation_system.calculate_corporate_tax(profit, rate)

    def record_revenue(self, result: TaxCollectionResult) -> None:
        """
        Updates internal ledgers based on a verified tax collection result.
        """
        if not result['success'] or result['amount_collected'] <= 0:
            return

        amount = result['amount_collected']
        tax_type = result['tax_type']
        # payer_id is available in result but not currently used for aggregate stats

        cur = result.get('currency', DEFAULT_CURRENCY)

        # Initialize currency buckets if new currency encountered
        if cur not in self.total_collected_tax:
            self.total_collected_tax[cur] = 0.0
        if cur not in self.revenue_this_tick:
            self.revenue_this_tick[cur] = 0.0

        # Update accumulators
        self.total_collected_tax[cur] += amount
        self.revenue_this_tick[cur] += amount

        # Update tax type breakdown (all-time)
        self.tax_revenue[tax_type] = (
            self.tax_revenue.get(tax_type, 0.0) + amount
        )

        # Update tick stats
        current_breakdown = self.current_tick_stats["tax_revenue"]
        current_breakdown[tax_type] = current_breakdown.get(tax_type, 0.0) + amount

        self.current_tick_stats["total_collected"] += amount

    def get_revenue_this_tick(self) -> Dict[CurrencyCode, float]:
        """Returns the total revenue collected in the current tick."""
        return self.revenue_this_tick.copy()

    def get_revenue_breakdown_this_tick(self) -> Dict[str, float]:
        """Returns the breakdown of revenue by tax type for the current tick."""
        return self.current_tick_stats["tax_revenue"].copy()

    def reset_tick_flow(self) -> None:
        """Resets the per-tick revenue accumulators."""
        # Reset revenue for this tick.
        # We re-initialize with DEFAULT_CURRENCY: 0.0 to match initialization state,
        # but empty dict is also valid as record_revenue handles missing keys.
        # Keeping consistent with __init__.
        self.revenue_this_tick = {DEFAULT_CURRENCY: 0.0}

        self.current_tick_stats = {
            "tax_revenue": {},
            "total_collected": 0.0
        }
