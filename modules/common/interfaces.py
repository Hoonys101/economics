from typing import Protocol, List, Dict, Any, Optional, runtime_checkable
from modules.system.api import CurrencyCode

@runtime_checkable
class IPropertyOwner(Protocol):
    """Protocol for agents that can own real estate properties."""
    owned_properties: List[int]

    def add_property(self, property_id: int) -> None:
        ...

    def remove_property(self, property_id: int) -> None:
        ...

@runtime_checkable
class IResident(Protocol):
    """Protocol for agents that can reside in a property."""
    residing_property_id: Optional[int]
    is_homeless: bool

@runtime_checkable
class IMortgageBorrower(Protocol):
    """Protocol for agents that can apply for a mortgage."""
    id: int
    assets: Dict[CurrencyCode, float]
    current_wage: float
