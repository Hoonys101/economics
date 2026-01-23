from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING, Deque

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.dtos import LeisureEffectDTO, StressScenarioConfig
    from modules.household.dtos import (
        CloningRequestDTO,
        EconContextDTO,
        SocialContextDTO,
        HouseholdStateDTO,
    )


class IBioComponent(ABC):
    """Interface for Biological Component."""

    @property
    @abstractmethod
    def age(self) -> float: ...

    @property
    @abstractmethod
    def gender(self) -> str: ...

    @abstractmethod
    def clone(self, request: CloningRequestDTO) -> Household: ...

    @abstractmethod
    def run_lifecycle(self, context: Dict[str, Any]): ...


class IEconComponent(ABC):
    """Interface for Economic Component."""

    @property
    @abstractmethod
    def assets(self) -> float: ...

    @abstractmethod
    def adjust_assets(self, delta: float) -> None: ...

    @abstractmethod
    def consume(self, item_id: str, quantity: float, current_time: int) -> Any: ...

    @abstractmethod
    def orchestrate_economic_decisions(
        self,
        context: EconContextDTO,
        orders: List[Any],
        stress_scenario_config: Optional[StressScenarioConfig] = None,
    ): ...

    # --- Phase 23: Inflation Expectation & Price Memory ---
    @property
    @abstractmethod
    def expected_inflation(self) -> Dict[str, float]: ...

    @property
    @abstractmethod
    def perceived_avg_prices(self) -> Dict[str, float]: ...

    @property
    @abstractmethod
    def price_history(self) -> Dict[str, Deque[float]]: ...

    @property
    @abstractmethod
    def adaptation_rate(self) -> float: ...

    @abstractmethod
    def update_perceived_prices(
        self,
        market_data: Dict[str, Any],
        stress_scenario_config: Optional[StressScenarioConfig] = None,
    ) -> None:
        """
        Calculates and updates the agent's inflation expectation and
        perceived average prices based on market data.
        """
        ...


class ISocialComponent(ABC):
    """Interface for Social Component."""

    @abstractmethod
    def calculate_social_status(self) -> None: ...

    @abstractmethod
    def update_political_opinion(self) -> None: ...

    @abstractmethod
    def apply_leisure_effect(
        self, leisure_hours: float, consumed_items: Dict[str, float]
    ) -> LeisureEffectDTO: ...
