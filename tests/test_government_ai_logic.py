
import unittest
from unittest.mock import MagicMock
from simulation.ai.government_ai import GovernmentAI

class TestGovernmentAILogic(unittest.TestCase):
    def setUp(self):
        self.mock_agent = MagicMock()
        self.mock_config = MagicMock()
        self.mock_agent.sensory_data = MagicMock()

        # Configure Config
        self.mock_config.TARGET_INFLATION_RATE = 0.02
        self.mock_config.TARGET_UNEMPLOYMENT_RATE = 0.04
        self.mock_config.AI_EPSILON = 0.1
        self.mock_config.RL_DISCOUNT_FACTOR = 0.95
        self.mock_config.RL_LEARNING_RATE = 0.1

        # Configure Agent defaults
        self.mock_agent.id = "gov_test"
        self.mock_agent.assets = -600.0 # Debt Ratio 0.6 (Ideal)

        self.ai = GovernmentAI(self.mock_agent, self.mock_config)

    def test_get_state_ideal(self):
        """Test State Discretization for Ideal Conditions"""
        # Setup Sensory DTO for Ideal conditions
        self.mock_agent.sensory_data.inflation_sma = 0.02
        self.mock_agent.sensory_data.unemployment_sma = 0.04
        self.mock_agent.sensory_data.gdp_growth_sma = 0.0
        self.mock_agent.sensory_data.current_gdp = 1000.0

        # Inflation: 0.02 (Target 0.02) -> Gap 0.0 -> Ideal (1)
        # Unemp: 0.04 (Target 0.04) -> Gap 0.0 -> Ideal (1)
        # GDP Growth: 0.0 -> Ideal (1)
        # Debt: 600/1000 = 0.6 -> Gap 0.0 -> Ideal (1)

        expected_state = (1, 1, 1, 1)
        state = self.ai._get_state()
        self.assertEqual(state, expected_state)

    def test_get_state_high_inflation_low_unemp(self):
        """Test Discretization for High Inflation, Low Unemployment"""
        # Setup Sensory DTO
        self.mock_agent.sensory_data.inflation_sma = 0.05
        self.mock_agent.sensory_data.unemployment_sma = 0.02
        self.mock_agent.sensory_data.gdp_growth_sma = 0.05
        self.mock_agent.sensory_data.current_gdp = 1050.0

        # Debt: 600/1050 = 0.57 -> Gap -0.03 -> Ideal (within +/- 0.05)

        # Inf: 0.05 - 0.02 = 0.03 > 0.01 -> High (2)
        # Unemp: 0.02 - 0.04 = -0.02 < -0.01 -> Low (0)
        # GDP Growth: 0.05 > 0.005 -> High (2)
        # Debt: Ideal (1)

        expected_state = (2, 0, 2, 1)
        state = self.ai._get_state()
        self.assertEqual(state, expected_state)

    def test_get_state_debt_crisis(self):
        """Test Debt Crisis State"""
        # Setup Sensory DTO for Ideal conditions (only testing debt)
        self.mock_agent.sensory_data.inflation_sma = 0.02
        self.mock_agent.sensory_data.unemployment_sma = 0.04
        self.mock_agent.sensory_data.gdp_growth_sma = 0.0
        self.mock_agent.sensory_data.current_gdp = 1000.0
        self.mock_agent.assets = -1000.0 # Debt 1000

        # Debt Ratio: 1000/1000 = 1.0 -> Gap 0.4 > 0.05 -> High (2)

        expected_state = (1, 1, 1, 2)
        state = self.ai._get_state()
        self.assertEqual(state, expected_state)

    def test_calculate_reward(self):
        """Test Reward Function Calculation"""
        # Scenario: High Inflation (0.05), Ideal Unemp (0.04), Ideal Debt (0.6)
        self.mock_agent.sensory_data.inflation_sma = 0.05
        self.mock_agent.sensory_data.unemployment_sma = 0.04
        self.mock_agent.sensory_data.current_gdp = 1000.0
        self.mock_agent.assets = -600.0

        # Inf Gap: 0.03 -> Sq: 0.0009
        # Unemp Gap: 0.0 -> Sq: 0.0
        # Debt Gap: 0.0 -> Sq: 0.0

        # Loss = 0.5 * 0.0009 = 0.00045
        # Reward = -0.00045 * 100 = -0.045

        reward = self.ai.calculate_reward()
        self.assertAlmostEqual(reward, -0.045, places=5)

    def test_learning_flow(self):
        """Test Q-Table Update Sequence"""
        # Setup Sensory DTO for Ideal conditions
        self.mock_agent.sensory_data.inflation_sma = 0.02
        self.mock_agent.sensory_data.unemployment_sma = 0.04
        self.mock_agent.sensory_data.gdp_growth_sma = 0.0
        self.mock_agent.sensory_data.current_gdp = 1000.0

        # Step 1: Decide Policy
        action = self.ai.decide_policy(current_tick=1)

        self.assertIsNotNone(self.ai.last_state)
        self.assertIsNotNone(self.ai.last_action_idx)
        previous_state = self.ai.last_state
        previous_action = self.ai.last_action_idx

        initial_q = self.ai.q_table.get_q_value(previous_state, previous_action)
        self.assertEqual(initial_q, 0.0)

        # Step 2: Update Learning (simulate outcome)
        # Under ideal conditions, reward should be 0.
        dummy_reward = -999.0 # This should be ignored by the learning function
        self.ai.update_learning_with_state(dummy_reward, current_tick=2)

        # Q-Value should not change as reward is 0
        updated_q = self.ai.q_table.get_q_value(previous_state, previous_action)
        self.assertAlmostEqual(updated_q, 0.0)

        # Test with Bad Condition to ensure learning happens
        # High Inflation -> Reward -0.045
        self.mock_agent.sensory_data.inflation_sma = 0.05
        self.ai.update_learning(dummy_reward, current_tick=3)

        # Previous Q was 0.0.
        # New = 0.0 + 0.1 * (-0.045 + 0.95*0.0 - 0.0) = -0.0045
        updated_q_2 = self.ai.q_table.get_q_value(previous_state, previous_action)
        self.assertAlmostEqual(updated_q_2, -0.0045, places=6)

if __name__ == '__main__':
    unittest.main()
