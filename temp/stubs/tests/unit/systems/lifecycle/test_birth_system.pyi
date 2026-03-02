import pytest
from modules.system.api import ICurrencyHolder as ICurrencyHolder
from typing import Any, Protocol

class IHousehold(Protocol):
    id: int
    age: float
    is_active: bool
    children_ids: list[int]
    portfolio: Any
    decision_engine: Any
    def get_balance(self, currency: str = 'USD') -> float: ...
    def get_assets_by_currency(self) -> dict[str, float]: ...

class TestBirthSystem:
    @pytest.fixture
    def birth_system(self): ...
    def test_process_births_with_factory_zero_sum(self, birth_system) -> None: ...
    def test_birth_system_requires_valid_protocol_context(self, birth_system) -> None: ...
