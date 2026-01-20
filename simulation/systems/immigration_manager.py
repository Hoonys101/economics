import random
import logging
from typing import List, Any
from simulation.core_agents import Household, Talent
from simulation.ai.api import Personality
from simulation.ai.household_ai import HouseholdAI
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.ai_model import AIEngineRegistry

logger = logging.getLogger(__name__)

class ImmigrationManager:
    """
    Phase 20 Step 3: Immigration Manager
    Responsible for injecting new households based on labor and population metrics.
    """

    def __init__(self, config_module: Any):
        self.config = config_module

    def process_immigration(self, engine: Any) -> List[Household]:
        """
        Checks immigration conditions and generates new households if met.

        Conditions:
          1. Unemployment Rate < 5% (Labor Shortage)
          2. Job Vacancies > 0 (Demand Exists)
          3. Total Population < Threshold (Demographic Crisis)
        """
        # 1. Gather Metrics
        indicators = engine.tracker.get_latest_indicators()
        unemployment_rate = indicators.get("unemployment_rate", 1.0)

        job_vacancies = 0
        if "labor" in engine.markets:
             job_vacancies = engine.markets["labor"].get_total_demand()

        total_population = len([h for h in engine.households if h.is_active])
        pop_threshold = getattr(self.config, "POPULATION_IMMIGRATION_THRESHOLD", 80)

        # 2. Check Conditions
        condition_labor_shortage = unemployment_rate < 0.05
        condition_job_demand = job_vacancies > 0
        condition_pop_crisis = total_population < pop_threshold

        if condition_labor_shortage and condition_job_demand and condition_pop_crisis:
            batch_size = getattr(self.config, "IMMIGRATION_BATCH_SIZE", 5)
            logger.info(
                f"IMMIGRATION_TRIGGERED | Pop: {total_population}, Unemp: {unemployment_rate:.2%}, Vacancies: {job_vacancies}. Influx: {batch_size}",
                extra={"tick": engine.time, "tags": ["immigration"]}
            )

            new_immigrants = self._create_immigrants(engine, batch_size)
            return new_immigrants

        return []

    def _create_immigrants(self, engine: Any, count: int) -> List[Household]:
        """Generates a batch of new immigrant households."""
        new_households = []

        # Determine Value Orientations (same distribution as main.py)
        all_value_orientations = [
            "wealth_and_needs",
            "needs_and_growth",
            "needs_and_social_status",
        ]

        goods_data = engine.goods_data # Reuse from engine

        for _ in range(count):
            agent_id = engine.next_agent_id
            engine.next_agent_id += 1

            # Random Attributes
            initial_assets = random.uniform(3000.0, 5000.0)
            personality = random.choice(list(Personality))
            value_orientation = random.choice(all_value_orientations)
            risk_aversion = random.uniform(0.1, 10.0)

            # Education (Low Skilled: 0 or 1)
            education_level = random.choice([0, 1])

            # Setup AI Engine
            # Note: We need the ai_trainer from engine to get the shared engine instance
            ai_decision_engine_instance = engine.ai_trainer.get_engine(value_orientation)
            household_ai_instance = HouseholdAI(agent_id=agent_id, ai_decision_engine=ai_decision_engine_instance)

            household_decision_engine = AIDrivenHouseholdDecisionEngine(
                ai_engine=household_ai_instance, config_module=self.config
            )

            # Initialize Needs (Simplified version of main.py logic)
            initial_needs = {
                "survival": 60.0,
                "social": 20.0,
                "improvement": 10.0,
                "asset": 10.0,
                "imitation_need": 15.0,
                "labor_need": 0.0,
                "liquidity_need": 50.0
            }

            # Create Household
            # Talent is randomized
            talent = Talent(max(0.5, random.gauss(1.0, 0.2)), {})

            household = Household(
                id=agent_id,
                talent=talent,
                goods_data=goods_data,
                initial_assets=initial_assets,
                initial_needs=initial_needs,
                decision_engine=household_decision_engine,
                value_orientation=value_orientation,
                personality=personality,
                config_module=self.config,
                risk_aversion=risk_aversion,
                logger=logger
            )

            # Set specific immigrant traits
            household.education_level = education_level
            household.gender = random.choice(["M", "F"])
            household.age = random.randint(20, 35) # Young workforce

            # Initial Inventory (Survival Kit)
            household.inventory["basic_food"] = 5.0

            new_households.append(household)

        return new_households
