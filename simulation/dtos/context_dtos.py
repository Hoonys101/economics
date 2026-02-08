from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from modules.system.api import MarketContextDTO, CurrencyCode

@dataclass
class PayrollProcessingContext:
    """
    Context for HREngine payroll processing.
    Contains all necessary data to process payroll without accessing Agent objects.
    """
    tax_rates: Dict[str, float]
    survival_cost: float
    market_context: MarketContextDTO
    government_id: Optional[int]
    settlement_system: Any # Should be ISettlementSystem protocol

@dataclass
class FinancialTransactionContext:
    """
    Context for FinanceEngine transaction generation.
    """
    government_id: Optional[int]
    tax_rates: Dict[str, float]
    market_context: MarketContextDTO
    shareholder_registry: Any # IShareholderRegistry protocol

@dataclass
class SalesContext:
    """
    Context for SalesEngine operations.
    """
    market_context: MarketContextDTO
    government_id: Optional[int]
    inventory_quantity: float
