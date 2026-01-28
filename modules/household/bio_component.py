from __future__ import annotations
from typing import Any, Dict, TYPE_CHECKING
import random
import logging

from modules.household.api import IBioComponent
from modules.household.dtos import BioStateDTO

if TYPE_CHECKING:
    from simulation.dtos.config_dtos import HouseholdConfigDTO

logger = logging.getLogger(__name__)

class BioComponent(IBioComponent):
    """
    Stateless component managing biological aspects of the Household.
    Operates on BioStateDTO.
    """

    def age_one_tick(self, state: BioStateDTO, config: HouseholdConfigDTO, current_tick: int) -> BioStateDTO:
        """
        Ages the agent and checks for natural death.
        Returns a new (or modified copy) BioStateDTO.
        """
        new_state = state.copy()

        ticks_per_year = config.ticks_per_year

        new_state.age += 1.0 / ticks_per_year

        # Natural Death Check
        age_death_probabilities = {
            60: 0.01,
            70: 0.02,
            80: 0.05,
            90: 0.15,
            100: 0.50,
        }

        death_prob_per_year = 0.0
        for age_threshold, prob in age_death_probabilities.items():
            if new_state.age >= age_threshold:
                death_prob_per_year = prob

        if death_prob_per_year > 0:
            death_prob_per_tick = death_prob_per_year / ticks_per_year
            if random.random() < death_prob_per_tick:
                new_state.is_active = False
                logger.info(f"BIO_DEATH | Agent {new_state.id} died of natural causes at age {new_state.age:.1f}")

        return new_state

    def create_offspring_demographics(self, state: BioStateDTO, new_id: int, current_tick: int, config: HouseholdConfigDTO) -> Dict[str, Any]:
        """
        Creates demographic data for a new agent (mitosis).
        Logic migrated from DemographicsComponent.
        """
        return {
            "generation": state.generation + 1,
            "parent_id": state.id,
            "initial_age": 0.0,
            "gender": random.choice(["M", "F"])
        }
