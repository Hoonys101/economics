from __future__ import annotations
from typing import List, Dict, Any, Optional
from modules.scenarios.api import (
    IScenario, IScenarioJudge, IScenarioBuilder, 
    ScenarioStrategy, Category, Tier
)
from modules.system.api import IWorldState

class BaseJudge:
    """
    Legacy compatibility base class that satisfies IScenarioJudge.
    """
    def __init__(self, tier: Tier, name: str):
        self._tier = tier
        self._name = name

    @property
    def tier(self) -> Tier:
        return self._tier

    @property
    def name(self) -> str:
        return self._name

    def judge(self, world_state: IWorldState) -> bool:
        """To be implemented by subclasses."""
        return True

    def get_metrics(self, world_state: IWorldState) -> Dict[str, Any]:
        """To be implemented by subclasses."""
        return {}

class ScenarioImplementation:
    """
    Implementation of IScenario protocol.
    """
    def __init__(self, strategy: ScenarioStrategy):
        self._strategy = strategy
        self._judges: List[IScenarioJudge] = []

    @property
    def strategy(self) -> ScenarioStrategy:
        return self._strategy

    @property
    def judges(self) -> List[IScenarioJudge]:
        return self._judges

    def add_judge(self, judge: IScenarioJudge):
        self._judges.append(judge)

class ScenarioBuilder:
    """
    Implementation of IScenarioBuilder protocol.
    Pure domain logic, no direct file I/O.
    """
    def __init__(self):
        self._strategy: Optional[ScenarioStrategy] = None
        self._judges: List[IScenarioJudge] = []

    def with_strategy(self, strategy: ScenarioStrategy) -> ScenarioBuilder:
        self._strategy = strategy
        return self

    def add_judge(self, judge: IScenarioJudge) -> ScenarioBuilder:
        self._judges.append(judge)
        return self

    def build(self) -> IScenario:
        if not self._strategy:
            raise ValueError("ScenarioStrategy must be provided before building.")
        
        scenario = ScenarioImplementation(self._strategy)
        for judge in self._judges:
            scenario.add_judge(judge)
        return scenario
