from dataclasses import dataclass, field as field
from modules.system.api import CurrencyCode as CurrencyCode, MarketContextDTO as MarketContextDTO
from typing import Any

@dataclass
class PayrollProcessingContext:
    """
    Context for HREngine payroll processing.
    Contains all necessary data to process payroll without accessing Agent objects.
    """
    tax_rates: dict[str, float]
    survival_cost: float
    market_context: MarketContextDTO
    government_id: int | None
    settlement_system: Any

@dataclass
class FinancialTransactionContext:
    """
    Context for FinanceEngine transaction generation.
    """
    government_id: int | None
    tax_rates: dict[str, float]
    market_context: MarketContextDTO
    shareholder_registry: Any

@dataclass
class SalesContext:
    """
    Context for SalesEngine operations.
    """
    market_context: MarketContextDTO
    government_id: int | None
    inventory_quantity: float
