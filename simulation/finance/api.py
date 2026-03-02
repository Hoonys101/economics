from typing import Protocol, runtime_checkable, Optional, Dict, Any, TypedDict, Union, List
from modules.finance.api import IFinancialAgent, ISettlementSystem, IMonetaryAuthority
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

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
    metadata: Optional[Dict[str, Any]]

@runtime_checkable
class IMintingSystem(Protocol):
    """
    Protocol for systems capable of minting currency (God Mode / Central Bank Injection).
    This capability is distinct from standard settlement to enforce Zero-Sum integrity elsewhere.
    """
    def create_and_transfer(self, source_authority: Any, destination: Any, amount: int, reason: str, tick: int, currency: str = DEFAULT_CURRENCY) -> Any:
        ...

# Legacy Aliases to ensure backward compatibility while migrating to modules.finance.api protocols
ISettlementSystem = ISettlementSystem
IMonetaryAuthority = IMonetaryAuthority
