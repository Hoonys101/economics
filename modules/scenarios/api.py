from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Any, Protocol, runtime_checkable
from pathlib import Path

# Note: Using localized import to avoid circular dependencies in the future
# if world_state starts depending on this api.
from modules.system.api import IWorldState

class Category(Enum):
    MONETARY = auto()     # M: M2 Integrity, Liquidity
    SOCIAL = auto()       # S: Inequality, Labor
    TECHNOLOGY = auto()   # T: TFP, Innovation
    CRISIS = auto()       # C: Bank Runs, Default
    POLITICAL = auto()    # P: Institutional Shocks (New)

class Tier(Enum):
    PHYSICS = 1           # System Integrity (M2 Delta, etc.)
    MACRO = 2             # Economic Health (GDP, etc.)
    MICRO = 3             # Agent Behavior (Panic, etc.)

@dataclass(frozen=True)
class ScenarioStrategy:
    """
    Pure Data Transfer Object defining the parameters and configuration 
    of a scenario. Strictly separated from execution logic.
    """
    id: str
    category: Category
    config_params: Dict[str, Any] = field(default_factory=dict)
    duration_ticks: int = 100

@dataclass(frozen=True)
class ScenarioOutcome:
    """
    Immutable DTO representing the evaluation result of a scenario.
    """
    scenario_id: str
    category: Category
    success: bool
    metrics: Dict[str, Any] = field(default_factory=dict)
    anomalies: List[str] = field(default_factory=list)

@runtime_checkable
class IScenarioJudge(Protocol):
    """
    Protocol for evaluating a specific aspect or tier of a scenario.
    Replaces the legacy BaseJudge ABC to eliminate God Class coupling.
    """
    @property
    def tier(self) -> Tier:
        ...
    
    @property
    def name(self) -> str:
        ...

    def judge(self, world_state: IWorldState) -> bool:
        """Evaluate the world state and return success/failure."""
        ...

    def get_metrics(self, world_state: IWorldState) -> Dict[str, Any]:
        """Harvest specific metrics relevant to this judge."""
        ...

@runtime_checkable
class IScenario(Protocol):
    """
    Protocol representing a built scenario, combining strategy data and execution judges.
    """
    @property
    def strategy(self) -> ScenarioStrategy:
        ...
        
    @property
    def judges(self) -> List[IScenarioJudge]:
        ...

@runtime_checkable
class IScenarioBuilder(Protocol):
    """
    Protocol for constructing Scenarios without coupling to I/O or file paths.
    Enforces Domain Logic Purity.
    """
    def with_strategy(self, strategy: ScenarioStrategy) -> IScenarioBuilder:
        ...

    def add_judge(self, judge: IScenarioJudge) -> IScenarioBuilder:
        ...

    def build(self) -> IScenario:
        ...

@runtime_checkable
class IScenarioLoader(Protocol):
    """
    Protocol for loading Scenario Strategies from external sources (e.g., JSON).
    Strictly separates I/O from execution and logic.
    """
    def load_strategy(self, source_id: str, raw_data: Dict[str, Any]) -> ScenarioStrategy:
        """Parses raw dictionary data into a valid frozen ScenarioStrategy."""
        ...

    def load_from_file(self, filepath: Path) -> ScenarioStrategy:
        """Loads and parses a scenario configuration from a JSON file."""
        ...

@runtime_checkable
class IJudgeFactory(Protocol):
    """
    Protocol for resolving and instantiating IScenarioJudge implementations
    based on ScenarioStrategy parameters, preventing hardcoded imports and God classes.
    """
    def create_judges(self, strategy: ScenarioStrategy) -> List[IScenarioJudge]:
        ...
