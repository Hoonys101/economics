from modules.system.api import CurrencyCode as CurrencyCode
from typing import Any, Protocol

class IPropertyOwner(Protocol):
    """Protocol for agents that can own real estate properties."""
    owned_properties: list[int]
    def add_property(self, property_id: int) -> None: ...
    def remove_property(self, property_id: int) -> None: ...

class IResident(Protocol):
    """Protocol for agents that can reside in a property."""
    residing_property_id: int | None
    is_homeless: bool

class IMortgageBorrower(Protocol):
    """Protocol for agents that can apply for a mortgage."""
    id: int
    assets: dict[CurrencyCode, float]
    current_wage: float

class IInvestor(Protocol):
    """Protocol for agents that hold a portfolio of assets."""
    portfolio: Any

class IIssuer(Protocol):
    """Protocol for entities that can issue shares."""
    id: int
    treasury_shares: float
    total_shares: float
