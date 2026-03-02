import pytest
from modules.finance.api import ILiquidatable as ILiquidatable
from typing import Any, Protocol

class IFirm(Protocol):
    id: int
    is_active: bool
    hr_state: Any
    def get_all_items(self) -> dict[str, float]: ...

class IHousehold(Protocol):
    id: int
    is_active: bool
    inventory: dict[str, float]
    def get_all_items(self) -> dict[str, float]: ...

class TestDeathSystemPerformance:
    @pytest.fixture
    def death_system(self): ...
    def test_localized_agent_removal(self, death_system) -> None:
        """
        Verifies that DeathSystem removes agents via localized deletion (O(1))
        instead of rebuilding the entire agents dictionary (O(N)).
        """
