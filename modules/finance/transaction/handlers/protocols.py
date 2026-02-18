from typing import Protocol, runtime_checkable, Any

@runtime_checkable
class ISolvent(Protocol):
    """Protocol for agents that can check their own solvency."""
    @property
    def assets(self) -> float:
        ...

    def check_solvency(self, government: Any) -> None:
        ...

@runtime_checkable
class ITaxCollector(Protocol):
    """Protocol for entities that can calculate and collect taxes (e.g., Government)."""

    def calculate_income_tax(self, income: int, deduction: int) -> int:
        ...

    def collect_tax(self, amount: int, tax_type: str, payer: Any, current_tick: int) -> Any:
        ...

    def record_revenue(self, data: Any) -> None:
        ...
