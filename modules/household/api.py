from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.dtos import LeisureEffectDTO
    from modules.household.dtos import CloningRequestDTO, EconContextDTO, SocialContextDTO, HouseholdStateDTO

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
    def orchestrate_economic_decisions(self, context: EconContextDTO, orders: List[Any]): ...

class ISocialComponent(ABC):
    """Interface for Social Component."""

    @abstractmethod
    def calculate_social_status(self) -> None: ...

    @abstractmethod
    def update_political_opinion(self) -> None: ...

    @abstractmethod
    def apply_leisure_effect(self, leisure_hours: float, consumed_items: Dict[str, float]) -> LeisureEffectDTO: ...
