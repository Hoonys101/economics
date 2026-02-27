from modules.finance.api import IFinancialAgent as IFinancialAgent, IMonetaryAuthority, ISettlementSystem
from modules.system.api import CurrencyCode as CurrencyCode, DEFAULT_CURRENCY as DEFAULT_CURRENCY
from typing import Any, Protocol, TypedDict

class ITransaction(TypedDict):
    """
    Represents a financial transaction result.
    Compatible with simulation.models.Transaction fields.
    """
    buyer_id: int
    seller_id: int
    item_id: str
    quantity: float
    price: float
    market_id: str
    transaction_type: str
    time: int
    metadata: dict[str, Any] | None

class IMintingSystem(Protocol):
    """
    Protocol for systems capable of minting currency (God Mode / Central Bank Injection).
    This capability is distinct from standard settlement to enforce Zero-Sum integrity elsewhere.
    """
    def mint_and_distribute(self, target_agent_id: int, amount: int, tick: int = 0, reason: str = 'god_mode_injection') -> bool: ...
ISettlementSystem = ISettlementSystem
IMonetaryAuthority = IMonetaryAuthority
