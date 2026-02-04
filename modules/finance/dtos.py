from typing import TypedDict, Dict, Optional, List, TypeAlias

CurrencyCode: TypeAlias = str

class MoneyDTO(TypedDict):
    """Represents a monetary value with its associated currency."""
    amount: float
    currency: CurrencyCode

class MultiCurrencyWalletDTO(TypedDict):
    """Represents a complete portfolio of assets, keyed by currency."""
    balances: Dict[CurrencyCode, float]

class InvestmentOrderDTO(TypedDict):
    """Defines an internal order for investment (e.g., R&D, Capex)."""
    order_type: str # e.g., "INVEST_RD", "INVEST_AUTOMATION"
    investment: MoneyDTO
    target_agent_id: Optional[int] # For M&A, etc.
