from modules.finance.api import IFinancialAgent as IFinancialAgent, IMonetaryAuthority, ISettlementSystem
from modules.system.api import CurrencyCode as CurrencyCode
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
    def create_and_transfer(self, source_authority: Any, destination: Any, amount: int, reason: str, tick: int, currency: str = ...) -> Any: ...
ISettlementSystem = ISettlementSystem
IMonetaryAuthority = IMonetaryAuthority
