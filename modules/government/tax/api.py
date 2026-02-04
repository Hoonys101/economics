# modules/government/tax/api.py
from typing import Protocol, Dict
from modules.finance.api import TaxCollectionResult
from modules.government.dtos import FiscalPolicyDTO
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

class ITaxService(Protocol):
    """
    Interface for the taxation service.
    """

    def calculate_tax_liability(self, policy: FiscalPolicyDTO, income: float) -> float:
        """Calculates the tax amount for a given income and fiscal policy."""
        ...

    def calculate_corporate_tax(self, profit: float, rate: float) -> float:
        """Calculates corporate tax based on profit and a flat rate."""
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

    def reset_tick_flow(self) -> None:
        """Resets the per-tick revenue accumulators."""
        ...
