import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))


import unittest
from unittest.mock import MagicMock
import logging
from simulation.core_agents import Household
from simulation.ai.household_ai import HouseholdAI
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.dtos import DecisionContext

# Configure logging
logging.basicConfig(level=logging.INFO)

class TestPopulationDynamics(unittest.TestCase):
    def setUp(self):
        # Mock Config
        self.config_module = MagicMock()
        self.config_module.REPRODUCTION_AGE_START = 20
        self.config_module.REPRODUCTION_AGE_END = 45
        self.config_module.CHILDCARE_TIME_REQUIRED = 8.0
        self.config_module.HOUSEWORK_BASE_HOURS = 2.0
        self.config_module.EDUCATION_COST_MULTIPLIERS = {
            0: 1.0, 1: 1.5, 2: 2.2, 3: 3.5, 4: 5.0, 5: 8.0
        }
        self.config_module.MASLOW_SURVIVAL_THRESHOLD = 50.0
        self.config_module.GOODS = {} # Minimal goods

        # Setup AI Decision Engine Mock
        self.ai_decision_engine = MagicMock()
        self.ai_decision_engine.config_module = self.config_module

        # Setup AI Engine
        self.ai_engine = HouseholdAI(
            agent_id="test_hh",
            ai_decision_engine=self.ai_decision_engine
        )

    def test_time_constraint(self):
        """
        Test that agent with high work hours rejects reproduction due to time poverty.
        """
        # Data Setup
        agent_data = {
            "age": 30.0,
            "is_employed": True,
            "current_wage": 10.0,
            "assets": 1000.0,
            "education_level": 0,
            "expected_wage": 10.0,
            "children_count": 0,
            "social_rank": 0.5,
            "needs": {"survival": 0.0},
        }
        market_data = {}

        # Case 1: Employed (Work 8h + Housework 2h + Childcare 8h = 18h < 24h) -> Feasible
        # Logic in HouseholdAI checks: 24 - 8 - 2 = 14 > 8. Returns True (statistically)
        # Note: Logic returns probabilistic result. But if time constraint fails, it returns False immediately.
        # We need to verify it *can* return True.

        # Force random to 0 for deterministic acceptance if probability > 0
        import random
        random.seed(42)

        # However, logic uses estimated work hours = 8.0 if employed.
        # 24 - 8 - 2 = 14. 14 > 8. Time constraint passes.

        decision = self.ai_engine.decide_reproduction(agent_data, market_data, 0)
        # Decision is probabilistic at the end, but should not be strictly False due to Time.
        # With social_rank 0.5 (Middle), prob is 0.01 or 0.05.

        # Let's adjust agent to be "Time Poor".
        # Assume we modify the constraint logic or config to simulate 16h work day?
        # Logic says "if is_employed: work_hours = 8.0".
        # We can't change that hardcoded 8.0 in logic easily without refactoring logic to take input.
        # BUT, if we increase HOUSEWORK or CHILDCARE requirement...

        self.config_module.CHILDCARE_TIME_REQUIRED = 16.0
        # 24 - 8 - 2 = 14 < 16. Should strictly return False.

        decision = self.ai_engine.decide_reproduction(agent_data, market_data, 0)
        self.assertFalse(decision, "Should reject due to time poverty (Childcare 16h)")

    def test_expectation_mismatch(self):
        """
        Test that high education agent with low income rejects reproduction.
        """
        self.config_module.CHILDCARE_TIME_REQUIRED = 8.0 # Reset

        # Case: High Education (Level 5 -> Mult 8.0 -> Exp Wage 80.0)
        # Current Wage: 10.0 (Low)
        # Satisfaction Ratio = (10*8) / (80*8) = 80 / 640 = 0.125
        # 0.125 < 0.8 -> Dissatisfied.
        # Social Rank 0.8 (Upper Class expectation?) or Middle?
        # If Social Rank is High (0.8), and Dissatisfied -> K-Strategy says "Not good enough" -> Prob 0.0

        agent_data = {
            "age": 30.0,
            "is_employed": True,
            "current_wage": 10.0,
            "assets": 1000.0,
            "education_level": 5, # High Expectation
            "expected_wage": 80.0, # 10 * 8
            "children_count": 0,
            "social_rank": 0.8, # High Rank
            "needs": {"survival": 0.0},
        }

        # Mock random to ensure we capture the logic branch
        decision = self.ai_engine.decide_reproduction(agent_data, {}, 0)
        self.assertFalse(decision, "Should reject due to expectation mismatch (High Edu, Low Wage)")

        # Contrast: Low Education (Level 0 -> Mult 1.0 -> Exp Wage 10.0)
        # Current Wage: 10.0
        # Ratio = 1.0. Satisfied.
        agent_data["education_level"] = 0
        agent_data["expected_wage"] = 10.0
        agent_data["social_rank"] = 0.8

        # If satisfied (>1.2 for upper class), prob is 0.05.
        # Ratio = 1.0. For Upper Class, >1.2 needed. So still 0.0.
        # Let's lower rank to Middle (0.5).
        agent_data["social_rank"] = 0.5
        # Middle class satisfied if > 1.0. Ratio is 1.0. > 1.0? No, == 1.0.
        # Let's boost wage slightly to 11.0.
        agent_data["current_wage"] = 11.0
        # Ratio = 88 / 80 = 1.1 > 1.0.
        # Prob = 0.05.

        # Since probabilistic, we run multiple times to check if True is *possible*
        success = False
        for _ in range(100):
            if self.ai_engine.decide_reproduction(agent_data, {}, 0):
                success = True
                break
        self.assertTrue(success, "Should eventually reproduce if satisfied")

if __name__ == '__main__':
    unittest.main()
