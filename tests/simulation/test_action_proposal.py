
import unittest
from unittest.mock import MagicMock, patch

from simulation.decisions.action_proposal import ActionProposalEngine

class TestActionProposalEngine(unittest.TestCase):
    def setUp(self):
        self.mock_config_module = MagicMock()
        self.mock_config_manager = MagicMock()

    def test_propose_household_actions_loads_consumables_from_config_manager(self):
        # Arrange
        self.mock_config_manager.get.return_value = ["test_food", "test_luxury_food"]
        self.mock_config_module.HOUSEHOLD_ASSETS_THRESHOLD_FOR_LABOR_SUPPLY = 200
        self.mock_config_module.FORCED_LABOR_EXPLORATION_PROBABILITY = 0.0 # Don't force exploration
        self.mock_config_module.GOODS_MARKET_SELL_PRICE = 10

        engine = ActionProposalEngine(
            config_module=self.mock_config_module,
            config_manager=self.mock_config_manager,
            n_action_samples=1,
        )

        mock_agent = MagicMock()
        mock_agent.id = 1
        mock_agent.assets = 100
        mock_agent.is_employed = False
        mock_agent.perceived_avg_prices = {}

        # Act
        with patch('random.choice') as mock_random_choice, \
             patch('random.random') as mock_random_value:
            mock_random_value.return_value = 0.6  # This will prevent exploring the labor market
            mock_random_choice.return_value = "test_food"
            engine._propose_household_actions(mock_agent, 0)

        # Assert
        self.mock_config_manager.get.assert_called_once_with('simulation.consumables')
        mock_random_choice.assert_called_with(["test_food", "test_luxury_food"])

if __name__ == '__main__':
    unittest.main()
