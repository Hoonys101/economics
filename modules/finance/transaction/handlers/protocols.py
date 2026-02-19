from typing import Protocol, runtime_checkable, Any, Optional

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

    def record_revenue(self, data: Any) -> None:
        ...

@runtime_checkable
class IIncomeTracker(Protocol):
    """Protocol for entities that track their income sources."""
    def add_labor_income(self, amount: int) -> None:
        ...

@runtime_checkable
class IConsumptionTracker(Protocol):
    """Protocol for entities that track their consumption expenditure."""
    def add_consumption_expenditure(self, amount: int, item_id: Optional[str] = None) -> None:
        ...
