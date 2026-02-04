# modules/government/tax/api.py
from typing import Protocol, Dict
from modules.finance.api import TaxCollectionResult
from modules.government.dtos import FiscalPolicyDTO
from simulation.dtos.api import MarketSnapshotDTO
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

class ITaxService(Protocol):
    """
    Interface for the taxation service.
    """

    def determine_fiscal_stance(self, snapshot: MarketSnapshotDTO) -> FiscalPolicyDTO:
        """Determines the current fiscal policy based on market conditions."""
        ...

    def calculate_tax_liability(self, policy: FiscalPolicyDTO, income: float) -> float:
        """Calculates the tax amount for a given income and fiscal policy."""
        ...

    def calculate_corporate_tax(self, profit: float, rate: float) -> float:
        """Calculates corporate tax based on profit and a flat rate."""
        ...

    def calculate_wealth_tax(self, net_worth: float) -> float:
        """Calculates wealth tax based on net worth."""
        ...

    def record_revenue(self, result: TaxCollectionResult) -> None:
        """
        Updates internal ledgers based on a verified tax collection result.
        This method should be the single source of truth for tax revenue logging.
        """
        ...

    def get_revenue_this_tick(self) -> Dict[CurrencyCode, float]:
        """Returns the total revenue collected in the current tick."""
        ...

    def get_revenue_breakdown_this_tick(self) -> Dict[str, float]:
        """Returns the breakdown of revenue by tax type for the current tick."""
        ...

    def get_total_collected_this_tick(self) -> float:
        """Returns the total amount collected this tick (sum of all currencies/types)."""
        ...

    def get_tax_revenue(self) -> Dict[str, float]:
        """Returns the all-time tax revenue breakdown."""
        ...

    def get_total_collected_tax(self) -> Dict[CurrencyCode, float]:
        """Returns the all-time total collected tax by currency."""
        ...

    def reset_tick_flow(self) -> None:
        """Resets the per-tick revenue accumulators."""
        ...
