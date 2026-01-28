from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from simulation.dtos import LeisureEffectDTO, ConsumptionResult, LaborResult, StressScenarioConfig
    from simulation.dtos.config_dtos import HouseholdConfigDTO
    from simulation.models import Order
    from modules.household.dtos import (
        BioStateDTO, EconStateDTO, SocialStateDTO,
        CloningRequestDTO, EconContextDTO
    )

class IBioComponent(ABC):
    """Interface for stateless Biological Component."""

    @abstractmethod
    def age_one_tick(self, state: BioStateDTO, config: HouseholdConfigDTO, current_tick: int) -> BioStateDTO:
        """Ages the agent and checks for natural death."""
        pass

    @abstractmethod
    def create_offspring_demographics(self, state: BioStateDTO, new_id: int, current_tick: int, config: HouseholdConfigDTO) -> Dict[str, Any]:
        """Creates demographic data for a new agent (mitosis)."""
        pass

class IEconComponent(ABC):
    """Interface for stateless Economic Component."""

    @abstractmethod
    def consume(
        self,
        state: EconStateDTO,
        needs: Dict[str, float],
        item_id: str,
        quantity: float,
        current_time: int,
        goods_info: Dict[str, Any],
        config: HouseholdConfigDTO
    ) -> Tuple[EconStateDTO, Dict[str, float], ConsumptionResult]:
        """
        Consumes an item.
        Returns: (Updated Econ State, Updated Needs (dict), Consumption Result)
        """
        pass

    @abstractmethod
    def decide_and_consume(
        self,
        state: EconStateDTO,
        needs: Dict[str, float],
        current_time: int,
        goods_info_map: Dict[str, Any],
        config: HouseholdConfigDTO
    ) -> Tuple[EconStateDTO, Dict[str, float], Dict[str, float]]:
        """
        Decides what to consume from inventory based on needs and executes consumption.
        Returns: (Updated Econ State, Updated Needs, Consumed Items Dict)
        """
        pass

    @abstractmethod
    def work(
        self,
        state: EconStateDTO,
        hours: float,
        config: HouseholdConfigDTO
    ) -> Tuple[EconStateDTO, LaborResult]:
        """Executes work logic (non-financial)."""
        pass

    @abstractmethod
    def update_skills(self, state: EconStateDTO, config: HouseholdConfigDTO) -> EconStateDTO:
        """Updates labor skills based on experience."""
        pass

    @abstractmethod
    def orchestrate_economic_decisions(
        self,
        state: EconStateDTO,
        context: EconContextDTO,
        orders: List[Order],
        stress_scenario_config: Optional[StressScenarioConfig] = None,
        config: Optional[HouseholdConfigDTO] = None
    ) -> Tuple[EconStateDTO, List[Order]]:
        """Refines orders and updates internal economic state (e.g. shadow wages)."""
        pass

    @abstractmethod
    def update_perceived_prices(
        self,
        state: EconStateDTO,
        market_data: Dict[str, Any],
        goods_info_map: Dict[str, Any],
        stress_scenario_config: Optional[StressScenarioConfig],
        config: HouseholdConfigDTO
    ) -> EconStateDTO:
        """Updates inflation expectations and price memory."""
        pass

    @abstractmethod
    def prepare_clone_state(
        self,
        parent_state: EconStateDTO,
        parent_skills: Dict[str, Any],
        config: HouseholdConfigDTO
    ) -> Dict[str, Any]:
        """
        Prepares initial economic state for a clone (inheritance logic).
        Returns a dictionary of kwargs for Household initialization or EconState values.
        """
        pass

class ISocialComponent(ABC):
    """Interface for stateless Social Component."""

    @abstractmethod
    def calculate_social_status(
        self,
        state: SocialStateDTO,
        assets: float,
        luxury_inventory: Dict[str, float],
        config: HouseholdConfigDTO
    ) -> SocialStateDTO:
        """Calculates social status."""
        pass

    @abstractmethod
    def update_political_opinion(
        self,
        state: SocialStateDTO,
        survival_need: float
    ) -> SocialStateDTO:
        """Updates political approval based on needs."""
        pass

    @abstractmethod
    def apply_leisure_effect(
        self,
        state: SocialStateDTO,
        labor_skill: float,
        children_count: int,
        leisure_hours: float,
        consumed_items: Dict[str, float],
        config: HouseholdConfigDTO
    ) -> Tuple[SocialStateDTO, float, LeisureEffectDTO]:
        """
        Applies leisure effects.
        Returns: (Updated Social State, Updated Labor Skill (value), Result DTO)
        """
        pass

    @abstractmethod
    def update_psychology(
        self,
        state: SocialStateDTO,
        bio_needs: Dict[str, float],
        assets: float,
        durable_assets: List[Dict[str, Any]],
        goods_info_map: Dict[str, Any],
        config: HouseholdConfigDTO,
        current_tick: int,
        market_data: Optional[Dict[str, Any]]
    ) -> Tuple[SocialStateDTO, Dict[str, float], List[Dict[str, Any]], bool]:
        """
        Updates psychological state and needs.
        Returns: (Updated Social State, Updated Needs, Updated Durable Assets, Is Active (bool))
        """
        pass
