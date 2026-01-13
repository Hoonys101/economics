
import unittest
from unittest.mock import MagicMock
from simulation.ai.government_ai import GovernmentAI

class TestGovernmentAILogic(unittest.TestCase):
    def setUp(self):
        self.mock_agent = MagicMock()
        self.mock_config = MagicMock()

        # Configure Config
        self.mock_config.TARGET_INFLATION_RATE = 0.02
        self.mock_config.TARGET_UNEMPLOYMENT_RATE = 0.04
        self.mock_config.AI_EPSILON = 0.1
        self.mock_config.RL_DISCOUNT_FACTOR = 0.95
        self.mock_config.RL_LEARNING_RATE = 0.1

        # Configure Agent defaults
        self.mock_agent.id = "gov_test"
        self.mock_agent.price_history_shadow = [100.0, 102.0] # 2% Inflation (Ideal)
        self.mock_agent.potential_gdp = 1000.0
        self.mock_agent.assets = -600.0 # Debt Ratio 0.6 (Ideal)

        self.ai = GovernmentAI(self.mock_agent, self.mock_config)

    def test_get_state_ideal(self):
        """Test State Discretization for Ideal Conditions"""
        market_data = {
            "unemployment_rate": 0.04, # Ideal
            "total_production": 1000.0, # Ideal (Gap 0)
        }

        # Inflation: (102-100)/100 = 0.02 (Target 0.02) -> Gap 0.0 -> Ideal (1)
        # Unemp: 0.04 (Target 0.04) -> Gap 0.0 -> Ideal (1)
        # GDP: (1000-1000)/1000 = 0.0 -> Ideal (1)
        # Debt: 600/1000 = 0.6 -> Gap 0.0 -> Ideal (1)

        expected_state = (1, 1, 1, 1)
        state = self.ai._get_state(market_data)
        self.assertEqual(state, expected_state)

    def test_get_state_high_inflation_low_unemp(self):
        """Test Discretization for High Inflation, Low Unemployment"""
        # Inflation 5%
        self.mock_agent.price_history_shadow = [100.0, 105.0]

        market_data = {
            "unemployment_rate": 0.02, # Low (-2% Gap)
            "total_production": 1050.0, # High GDP (+5%)
        }
        # Debt: 600/1050 = 0.57 -> Gap -0.03 -> Ideal (within +/- 0.05)

        # Inf: 0.05 - 0.02 = 0.03 > 0.01 -> High (2)
        # Unemp: 0.02 - 0.04 = -0.02 < -0.01 -> Low (0)
        # GDP: 0.05 > 0.01 -> High (2)
        # Debt: Ideal (1)

        expected_state = (2, 0, 2, 1)
        state = self.ai._get_state(market_data)
        self.assertEqual(state, expected_state)

    def test_get_state_debt_crisis(self):
        """Test Debt Crisis State"""
        self.mock_agent.price_history_shadow = [100.0, 102.0] # Ideal
        self.mock_agent.assets = -1000.0 # Debt 1000

        market_data = {
            "unemployment_rate": 0.04,
            "total_production": 1000.0,
        }
        # Debt Ratio: 1000/1000 = 1.0 -> Gap 0.4 > 0.05 -> High (2)

        expected_state = (1, 1, 1, 2)
        state = self.ai._get_state(market_data)
        self.assertEqual(state, expected_state)

    def test_calculate_reward(self):
        """Test Reward Function Calculation"""
        # Scenario: High Inflation (0.05), Ideal Unemp (0.04), Ideal Debt (0.6)
        self.mock_agent.price_history_shadow = [100.0, 105.0] # Inf 0.05
        market_data = {
            "unemployment_rate": 0.04,
            "total_production": 1000.0
        }
        self.mock_agent.assets = -600.0

        # Inf Gap: 0.03 -> Sq: 0.0009
        # Unemp Gap: 0.0 -> Sq: 0.0
        # Debt Gap: 0.0 -> Sq: 0.0

        # Loss = 0.5 * 0.0009 = 0.00045
        # Reward = -0.00045 * 100 = -0.045

        reward = self.ai.calculate_reward(market_data)
        self.assertAlmostEqual(reward, -0.045, places=5)

    def test_learning_flow(self):
        """Test Q-Table Update Sequence"""
        market_data = {
            "unemployment_rate": 0.04,
            "total_production": 1000.0,
        }

        # Step 1: Decide Policy
        # Force epsilon to 0.0 to test specific q-value choice? Or just check attribute update.
        # Just check that last_state is updated.
        action = self.ai.decide_policy(market_data, current_tick=1)

        self.assertIsNotNone(self.ai.last_state)
        self.assertIsNotNone(self.ai.last_action_idx)
        previous_state = self.ai.last_state
        previous_action = self.ai.last_action_idx

        # Initial Q Value should be 0.0
        initial_q = self.ai.q_table.get_q_value(previous_state, previous_action)
        self.assertEqual(initial_q, 0.0)

        # Step 2: Update Learning (simulate outcome)
        # In the new logic, update_learning calculates reward internally based on market_data.
        # We need to setup market_data to produce a known reward.

        # Scenario: Ideal Conditions -> Reward 0.0 (Loss 0)
        # market_data is already set to ideal in setUp logic (via mock_agent defaults and input data)
        # However, test_learning_flow didn't setup mock_agent.price_history_shadow for ideal inflation specifically in this method?
        # It relies on setUp. setUp has [100, 102] -> Inf 0.02 (Ideal).
        # Unemp 0.04 (Ideal).
        # GDP 1000 (Ideal).
        # Debt Ratio 0.6 (Ideal).
        # So Reward should be -0.0.

        dummy_reward = -999.0 # Should be ignored
        self.ai.update_learning(dummy_reward, market_data, current_tick=2)

        # Check Q Value updated
        # New = Old + alpha * (RealReward + gamma*NextMax - Old)
        # RealReward = 0.0 (Ideal)
        # New = 0.0 + 0.1 * (0.0 + 0.95*0.0 - 0.0) = 0.0

        updated_q = self.ai.q_table.get_q_value(previous_state, previous_action)
        self.assertAlmostEqual(updated_q, 0.0)

        # Test with Bad Condition to ensure learning happens
        # Change market_data to High Inflation (Inf Gap 0.03 -> Sq 0.0009 -> Weighted 0.00045 -> Reward -0.00045)
        self.mock_agent.price_history_shadow = [100.0, 105.0]

        # We need to decide again to set last_state/action or re-use?
        # Let's re-use.
        self.ai.update_learning(dummy_reward, market_data, current_tick=3)

        # Now Reward is -0.045.
        # But wait, Q-table was updated in previous call.
        # Previous Q was 0.0.
        # New = 0.0 + 0.1 * (-0.045 + 0.95*0.0 - 0.0) = -0.0045
        updated_q_2 = self.ai.q_table.get_q_value(previous_state, previous_action)
        self.assertAlmostEqual(updated_q_2, -0.0045, places=6)

if __name__ == '__main__':
    unittest.main()
