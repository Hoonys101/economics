from __future__ import annotations
from typing import List, Dict, Any, Optional
import random
import logging

from modules.household.api import ILifecycleEngine, LifecycleInputDTO, LifecycleOutputDTO
from modules.household.dtos import BioStateDTO, CloningRequestDTO

logger = logging.getLogger(__name__)

class LifecycleEngine(ILifecycleEngine):
    """
    Stateless engine managing aging, death, and reproduction decisions.
    Logic migrated from HouseholdLifecycleMixin and BioComponent.
    """

    def process_tick(self, input_dto: LifecycleInputDTO) -> LifecycleOutputDTO:
        """
        Increments age, checks for natural death, and evaluates reproduction.
        """
        bio_state = input_dto.bio_state
        config = input_dto.config

        # 1. Aging Logic
        new_bio_state = bio_state.copy()
        ticks_per_year = float(config.ticks_per_year) if config.ticks_per_year > 0 else 100.0

        new_bio_state.age += 1.0 / ticks_per_year

        # 2. Natural Death Check
        # Logic from BioComponent.age_one_tick
        age_death_probabilities = {
            60: 0.01,
            70: 0.02,
            80: 0.05,
            90: 0.15,
            100: 0.50,
        }

        death_prob_per_year = 0.0
        # Determine applicable probability
        sorted_thresholds = sorted(age_death_probabilities.keys())
        for threshold in sorted_thresholds:
            if new_bio_state.age >= threshold:
                death_prob_per_year = age_death_probabilities[threshold]
            else:
                break # Since sorted, if age < threshold, break

        # Also check hard max age if defined, or just rely on prob
        if death_prob_per_year > 0:
            death_prob_per_tick = death_prob_per_year / ticks_per_year
            if random.random() < death_prob_per_tick:
                new_bio_state.is_active = False
                logger.info(f"BIO_DEATH | Agent {new_bio_state.id} died of natural causes at age {new_bio_state.age:.1f}")

        # 3. Reproduction Decision
        # Currently, LifecycleManager handles this externally via VectorizedHouseholdPlanner.
        # However, to support autonomy, we can include checks here.
        # For now, we return empty list unless we implement specific logic.
        # If we want to replicate VectorizedPlanner logic here for autonomy:
        # Check fertility, solvency, NPV.
        # But VectorizedPlanner does this efficiently for all agents.
        # So we leave it empty for now, relying on external trigger (LifecycleManager).
        cloning_requests: List[CloningRequestDTO] = []

        # Example logic placeholder:
        # if input_dto.bio_state.is_active and 20 <= new_bio_state.age <= 45:
        #     # Check resources...
        #     pass

        return LifecycleOutputDTO(
            bio_state=new_bio_state,
            cloning_requests=cloning_requests
        )

    def create_offspring_demographics(self, state: BioStateDTO, new_id: int, current_tick: int) -> Dict[str, Any]:
        """
        Helper to create demographic data for a new agent.
        Used by Household.clone().
        Logic from BioComponent.create_offspring_demographics.
        """
        return {
            "generation": state.generation + 1,
            "parent_id": state.id,
            "initial_age": 0.0,
            "gender": random.choice(["M", "F"])
        }
