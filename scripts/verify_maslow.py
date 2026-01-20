
import sys
import os
import unittest
from unittest.mock import MagicMock

# Add project root to path
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import config
from simulation.ai.household_ai import HouseholdAI
from simulation.schemas import HouseholdActionVector

class TestMaslowVerification(unittest.TestCase):
    def setUp(self):
        # Mock Decision Engine and Config
        self.mock_decision_engine = MagicMock()
        self.mock_decision_engine.config_module = config

        # Initialize HouseholdAI
        self.ai = HouseholdAI(
            agent_id="test_household",
            ai_decision_engine=self.mock_decision_engine
        )

        # Define goods list
        self.goods_list = ["basic_food", "clothing", "luxury_food", "education_service"]

        # Mock Q-Table managers to return a fixed action index (e.g., max aggressiveness)
        # to prove that Maslow logic overrides it.
        # Index 4 corresponds to 1.0 aggressiveness in AGGRESSIVENESS_LEVELS = [0.0, 0.25, 0.5, 0.75, 1.0]
        for item in self.goods_list:
            self.ai.q_consumption[item] = MagicMock()
            self.ai.action_selector.choose_action = MagicMock(return_value=4)

        self.ai.q_investment = MagicMock()
        self.ai.q_work = MagicMock()

    def test_maslow_gating_starving(self):
        print("\nTesting Maslow Gating: Starving State")

        # Mock Data: Survival Need > Threshold (50.0)
        agent_data = {
            "assets": 1000.0,
            "needs": {"survival": 80.0}, # Starving!
            "inventory": {}
        }
        market_data = {}

        # Execute Decision
        action_vector = self.ai.decide_action_vector(agent_data, market_data, self.goods_list)

        # Verify Results
        print(f"Action Vector: {action_vector}")

        # 1. Survival Goods (basic_food) should be aggressive (1.0)
        self.assertEqual(action_vector.consumption_aggressiveness.get("basic_food"), 1.0,
                         "Survival good (basic_food) should not be gated.")

        # 2. Non-Survival Goods (education_service) should be 0.0
        # education_service has utility {improvement: 15}, survival: 0 (implicit)
        self.assertEqual(action_vector.consumption_aggressiveness.get("education_service"), 0.0,
                         "Non-survival good (education_service) should be gated to 0.0.")

        # 3. Investment should be 0.0
        self.assertEqual(action_vector.investment_aggressiveness, 0.0,
                         "Investment should be gated to 0.0 when starving.")

        print("✅ Maslow Gating Verified: Starving agents focus on survival.")

    def test_maslow_gating_normal(self):
        print("\nTesting Maslow Gating: Normal State")

        # Mock Data: Survival Need < Threshold (50.0)
        agent_data = {
            "assets": 1000.0,
            "needs": {"survival": 20.0}, # Not Starving
            "inventory": {}
        }
        market_data = {}

        # Execute Decision
        action_vector = self.ai.decide_action_vector(agent_data, market_data, self.goods_list)

        # Verify Results
        print(f"Action Vector: {action_vector}")

        # 1. Non-Survival Goods (education_service) should NOT be gated
        self.assertEqual(action_vector.consumption_aggressiveness.get("education_service"), 1.0,
                         "Non-survival good (education_service) should NOT be gated when not starving.")

        # 3. Investment should NOT be 0.0 (since assets > 500)
        self.assertEqual(action_vector.investment_aggressiveness, 1.0,
                         "Investment should NOT be gated when not starving.")

        print("✅ Maslow Gating Verified: Normal agents can pursue other goals.")

if __name__ == '__main__':
    unittest.main()
