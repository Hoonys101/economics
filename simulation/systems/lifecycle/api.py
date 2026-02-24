from __future__ import annotations
from typing import Protocol, List, Any, Dict, runtime_checkable, TYPE_CHECKING
from simulation.dtos.api import SimulationState
from simulation.models import Transaction
from modules.finance.api import IFinancialEntity

@runtime_checkable
class ILifecycleSubsystem(Protocol):
    """
    Protocol for discrete lifecycle systems (Birth, Aging, Death).
    Adheres to SEO Pattern: Stateless execution on State DTO.
    """
    def execute(self, state: SimulationState) -> List[Transaction]:
        """
        Executes the lifecycle logic for the current tick.
        Returns a list of transactions (e.g., inheritance, fees) to be processed.
        """
        ...

@runtime_checkable
class IAgingSystem(ILifecycleSubsystem, Protocol):
    """
    Responsible for incrementing age, updating biological needs,
    and performing health/distress checks for all agents.
    """
    ...

@runtime_checkable
class IBirthSystem(ILifecycleSubsystem, Protocol):
    """
    Responsible for creating new agents (Households) via reproduction
    and handling immigration entry.
    """
    ...

@runtime_checkable
class IDeathSystem(ILifecycleSubsystem, Protocol):
    """
    Responsible for handling agent death, liquidation of assets,
    and inheritance processing.
    """
    ...

@runtime_checkable
class IFinanceEngine(Protocol):
    def check_bankruptcy(self, finance_state: Any, config: Any) -> None: ...

@runtime_checkable
class IAgingFirm(Protocol):
    id: Any
    is_active: bool
    age: int
    needs: Dict[str, float]
    wallet: IFinancialEntity
    finance_state: Any
    config: Any
    finance_engine: IFinanceEngine

    def get_all_items(self) -> Dict[str, Any]: ...
