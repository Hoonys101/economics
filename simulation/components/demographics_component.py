from __future__ import annotations
from typing import Dict, Any, Optional, List, TYPE_CHECKING
import random
import logging

from simulation.components.api import IDemographicsComponent

if TYPE_CHECKING:
    from simulation.core_agents import Household, Talent
    # from config import YourConfigModule # TBD: 실제 설정 모듈 경로로 변경

class DemographicsComponent:
    """Handles the demographic data and lifecycle logic for a Household."""

    def __init__(self, owner: "Household", initial_age: float, gender: str, generation: int = 0, parent_id: Optional[int] = None, config_module: Any = None):
        self._owner = owner
        self._age = initial_age
        self._gender = gender
        self._generation = generation
        self._parent_id = parent_id
        self._spouse_id: Optional[int] = None
        self._children_ids: List[int] = []

        self.config_module = config_module
        self.logger = owner.logger

    # --- Properties ---
    @property
    def owner(self) -> "Household":
        return self._owner

    @property
    def age(self) -> float:
        return self._age

    @age.setter
    def age(self, value: float) -> None:
        self._age = value

    @property
    def gender(self) -> str:
        return self._gender

    @gender.setter
    def gender(self, value: str) -> None:
        self._gender = value

    @property
    def generation(self) -> int:
        return self._generation

    @generation.setter
    def generation(self, value: int) -> None:
        self._generation = value

    @property
    def parent_id(self) -> Optional[int]:
        return self._parent_id

    @parent_id.setter
    def parent_id(self, value: Optional[int]) -> None:
        self._parent_id = value

    @property
    def spouse_id(self) -> Optional[int]:
        return self._spouse_id

    @spouse_id.setter
    def spouse_id(self, value: Optional[int]) -> None:
        self._spouse_id = value

    @property
    def children_ids(self) -> List[int]:
        return self._children_ids

    @property
    def children_count(self) -> int:
        return len(self._children_ids)

    # --- Methods ---
    def age_one_tick(self, current_tick: int) -> None:
        """Ages the agent by one tick and checks for death."""
        ticks_per_year = getattr(self.config_module, "TICKS_PER_YEAR", 100)
        self._age += 1.0 / ticks_per_year

        if self.handle_death(current_tick):
            self.logger.info(f"DEATH | Household {self.owner.id} has died at age {self._age:.1f}.")

    def handle_death(self, current_tick: int) -> bool:
        """
        There is a chance of death, which increases with age.
        If the agent dies, its is_active status is set to False.
        """

        # The chance of death per year, based on age.
        age_death_probabilities = {
            60: 0.01,
            70: 0.02,
            80: 0.05,
            90: 0.15,
            100: 0.50,
        }

        # Find the highest age threshold that the agent's age has surpassed
        # and get the corresponding death probability.
        death_prob_per_year = 0
        for age_threshold, prob in age_death_probabilities.items():
            if self._age >= age_threshold:
                death_prob_per_year = prob

        # If the agent's age has not surpassed any of the thresholds,
        # there is no chance of death.
        if death_prob_per_year == 0:
            return False

        # Convert the annual probability to a per-tick probability.
        ticks_per_year = getattr(self.config_module, "TICKS_PER_YEAR", 100)
        death_prob_per_tick = death_prob_per_year / ticks_per_year

        # Check if the agent dies.
        if random.random() < death_prob_per_tick:
            self.owner.is_active = False
            return True

        return False

    def set_spouse(self, spouse_id: int) -> None:
        self._spouse_id = spouse_id

    def add_child(self, child_id: int) -> None:
        if child_id not in self._children_ids:
            self._children_ids.append(child_id)

    def get_generational_similarity(self, talent_learning_rate_1: float, talent_learning_rate_2: float) -> float:
        """Calculates the generational/genetic similarity based on talent learning rates."""

        # A simple comparison of talents.
        talent_diff = abs(talent_learning_rate_1 - talent_learning_rate_2)
        similarity = max(0.0, 1.0 - talent_diff)
        return similarity

    def create_offspring_demographics(self, new_id: int, current_tick: int) -> Dict[str, Any]:
        """Creates the initial demographic attributes for an offspring."""
        return {
            "generation": self._generation + 1,
            "parent_id": self.owner.id,
            "initial_age": 0.0,
            "gender": random.choice(["M", "F"])
        }
