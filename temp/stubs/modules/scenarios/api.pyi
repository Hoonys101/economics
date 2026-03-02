from dataclasses import dataclass, field
from enum import Enum
from modules.system.api import IWorldState as IWorldState
from pathlib import Path
from typing import Any, Protocol

class Category(Enum):
    MONETARY = ...
    SOCIAL = ...
    TECHNOLOGY = ...
    CRISIS = ...
    POLITICAL = ...

class Tier(Enum):
    PHYSICS = 1
    MACRO = 2
    MICRO = 3

@dataclass(frozen=True)
class ScenarioStrategy:
    """
    Pure Data Transfer Object defining the parameters and configuration 
    of a scenario. Strictly separated from execution logic.
    """
    id: str
    category: Category
    config_params: dict[str, Any] = field(default_factory=dict)
    duration_ticks: int = ...

@dataclass(frozen=True)
class ScenarioOutcome:
    """
    Immutable DTO representing the evaluation result of a scenario.
    """
    scenario_id: str
    category: Category
    success: bool
    metrics: dict[str, Any] = field(default_factory=dict)
    anomalies: list[str] = field(default_factory=list)

class IScenarioJudge(Protocol):
    """
    Protocol for evaluating a specific aspect or tier of a scenario.
    Replaces the legacy BaseJudge ABC to eliminate God Class coupling.
    """
    @property
    def tier(self) -> Tier: ...
    @property
    def name(self) -> str: ...
    def judge(self, world_state: IWorldState) -> bool:
        """Evaluate the world state and return success/failure."""
    def get_metrics(self, world_state: IWorldState) -> dict[str, Any]:
        """Harvest specific metrics relevant to this judge."""

class IScenario(Protocol):
    """
    Protocol representing a built scenario, combining strategy data and execution judges.
    """
    @property
    def strategy(self) -> ScenarioStrategy: ...
    @property
    def judges(self) -> list[IScenarioJudge]: ...

class IScenarioBuilder(Protocol):
    """
    Protocol for constructing Scenarios without coupling to I/O or file paths.
    Enforces Domain Logic Purity.
    """
    def with_strategy(self, strategy: ScenarioStrategy) -> IScenarioBuilder: ...
    def add_judge(self, judge: IScenarioJudge) -> IScenarioBuilder: ...
    def build(self) -> IScenario: ...

class IScenarioLoader(Protocol):
    """
    Protocol for loading Scenario Strategies from external sources (e.g., JSON).
    Strictly separates I/O from execution and logic.
    """
    def load_strategy(self, source_id: str, raw_data: dict[str, Any]) -> ScenarioStrategy:
        """Parses raw dictionary data into a valid frozen ScenarioStrategy."""
    def load_from_file(self, filepath: Path) -> ScenarioStrategy:
        """Loads and parses a scenario configuration from a JSON file."""

class IJudgeFactory(Protocol):
    """
    Protocol for resolving and instantiating IScenarioJudge implementations
    based on ScenarioStrategy parameters, preventing hardcoded imports and God classes.
    """
    def create_judges(self, strategy: ScenarioStrategy) -> list[IScenarioJudge]: ...
