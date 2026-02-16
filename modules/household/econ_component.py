from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
from collections import deque, defaultdict
import math
import random
import logging

from modules.household.api import IEconComponent
from modules.household.dtos import EconStateDTO
from simulation.dtos import LaborResult, StressScenarioConfig
from simulation.models import Skill

if TYPE_CHECKING:
    from modules.simulation.dtos.api import HouseholdConfigDTO

logger = logging.getLogger(__name__)

class EconComponent(IEconComponent):
    """
    Stateless component managing economic aspects of the Household.
    Operates on EconStateDTO.
    """

    def update_wage_dynamics(self, state: EconStateDTO, config: HouseholdConfigDTO, is_employed: bool) -> EconStateDTO:
        new_state = state.copy()

        if is_employed:
            recovery_rate = config.wage_recovery_rate
            new_state.wage_modifier = min(1.0, new_state.wage_modifier * (1.0 + recovery_rate))
        else:
            decay_rate = config.wage_decay_rate
            floor_mod = config.reservation_wage_floor
            new_state.wage_modifier = max(floor_mod, new_state.wage_modifier * (1.0 - decay_rate))

        return new_state

    def work(self, state: EconStateDTO, hours: float, config: HouseholdConfigDTO) -> Tuple[EconStateDTO, LaborResult]:
        """
        Executes work logic (non-financial).
        Logic migrated from LaborManager.work.
        """
        new_state = state.copy()

        if not new_state.is_employed or new_state.employer_id is None:
            return new_state, LaborResult(hours_worked=0, income_earned=0)

        income = new_state.current_wage * hours
        # Note: We do NOT add assets here. TransactionProcessor handles wages.

        return new_state, LaborResult(hours_worked=hours, income_earned=income)

    def update_skills(self, state: EconStateDTO, config: HouseholdConfigDTO) -> EconStateDTO:
        """
        Updates labor skills based on experience.
        Logic migrated from LaborManager.update_skills.
        """
        new_state = state.copy()

        log_growth = math.log1p(new_state.education_xp) # ln(x+1)
        talent_factor = new_state.talent.base_learning_rate
        new_skill_val = 1.0 + (log_growth * talent_factor)

        new_state.labor_skill = new_skill_val

        return new_state

    def update_perceived_prices(
        self,
        state: EconStateDTO,
        market_data: Dict[str, Any],
        goods_info_map: Dict[str, Any],
        stress_scenario_config: Optional[StressScenarioConfig],
        config: HouseholdConfigDTO
    ) -> EconStateDTO:
        """
        Updates inflation expectations and price memory.
        """
        new_state = state.copy()
        goods_market = market_data.get("goods_market")
        if not goods_market:
            return new_state

        adaptive_rate = new_state.adaptation_rate
        if stress_scenario_config and stress_scenario_config.is_active:
            if stress_scenario_config.scenario_name == 'hyperinflation':
                if hasattr(stress_scenario_config, "inflation_expectation_multiplier"):
                     adaptive_rate *= stress_scenario_config.inflation_expectation_multiplier

        for item_id, good in goods_info_map.items():
            actual_price = goods_market.get(f"{item_id}_avg_traded_price")

            if actual_price is not None and actual_price > 0:
                history = new_state.price_history[item_id]
                if history:
                    last_price = history[-1]
                    if last_price > 0:
                        inflation_t = (actual_price - last_price) / last_price

                        old_expect = new_state.expected_inflation.get(item_id, 0.0)
                        new_expect = old_expect + adaptive_rate * (inflation_t - old_expect)
                        new_state.expected_inflation[item_id] = new_expect

                history.append(actual_price)

                old_perceived_price = new_state.perceived_avg_prices.get(
                    item_id, actual_price
                )
                update_factor = config.perceived_price_update_factor
                new_perceived_price = (
                    update_factor * actual_price
                ) + (
                    (1 - update_factor)
                    * old_perceived_price
                )
                new_state.perceived_avg_prices[item_id] = new_perceived_price

        return new_state

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
        # Logic migrated from Household.apply_child_inheritance

        # Skill Inheritance
        new_skills = {}
        for domain, skill in parent_skills.items():
            # Assuming skill is object with domain, value, observability
            new_skills[domain] = Skill(
                domain=domain,
                value=skill.value * 0.2,
                observability=skill.observability
            )

        education_level = min(parent_state.education_level, 1)
        expected_wage = parent_state.expected_wage * 0.8

        return {
            "skills": new_skills,
            "education_level": education_level,
            "expected_wage": expected_wage,
            "labor_skill": parent_state.labor_skill,
            "aptitude": parent_state.aptitude
        }
