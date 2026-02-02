import unittest
from unittest.mock import Mock, MagicMock, patch
from simulation.systems.firm_management import FirmSystem

class TestFirmManagementRefactor(unittest.TestCase):
    def setUp(self):
        self.mock_config = Mock()
        self.mock_config.STARTUP_COST = 1000.0
        self.mock_config.VISIONARY_MUTATION_RATE = 0.0
        self.mock_config.VALUE_ORIENTATION_WEALTH_AND_NEEDS = "WEALTH_AND_NEEDS"
        self.mock_config.VALUE_ORIENTATION_NEEDS_AND_GROWTH = "NEEDS_AND_GROWTH"
        self.mock_config.GOODS = {
            "food": {"sector": "PRIMARY", "inputs": {}},
        }
        self.mock_config.SERVICE_SECTORS = []
        self.mock_config.INITIAL_FIRM_LIQUIDITY_NEED_MEAN = 50.0
        self.mock_config.FIRM_DECISION_ENGINE = "AI_DRIVEN"

        self.firm_system = FirmSystem(self.mock_config)

        self.mock_simulation = MagicMock()
        self.mock_simulation.agents = {}
        self.mock_simulation.firms = []
        self.mock_simulation.households = []
        self.mock_simulation.markets = {}
        self.mock_simulation.stock_market = MagicMock()
        self.mock_simulation.ai_training_manager = MagicMock()
        self.mock_simulation.logger = MagicMock()
        self.mock_simulation.time = 123

    def test_spawn_firm_missing_settlement_system(self):
        """
        Verify that spawn_firm raises RuntimeError if settlement_system is missing.
        """
        self.mock_simulation.settlement_system = None

        household = MagicMock()
        household._econ_state.assets = 5000.0

        with patch('simulation.systems.firm_management.random.choice', return_value='food'), \
             patch('simulation.systems.firm_management.random.random', return_value=0.9), \
             patch('simulation.firms.Firm'), \
             patch('simulation.ai.firm_ai.FirmAI'), \
             patch('simulation.decisions.ai_driven_firm_engine.AIDrivenFirmDecisionEngine'):

            with self.assertRaisesRegex(RuntimeError, "SettlementSystem required for firm creation"):
                self.firm_system.spawn_firm(self.mock_simulation, household)

    def test_spawn_firm_transfer_failure(self):
        """
        Verify that spawn_firm returns None if transfer fails.
        """
        self.mock_simulation.settlement_system = MagicMock()
        self.mock_simulation.settlement_system.transfer.return_value = None # Failure

        household = MagicMock()
        household._econ_state.assets = 5000.0

        with patch('simulation.systems.firm_management.random.choice', return_value='food'), \
             patch('simulation.systems.firm_management.random.random', return_value=0.9), \
             patch('simulation.firms.Firm'), \
             patch('simulation.ai.firm_ai.FirmAI'), \
             patch('simulation.decisions.ai_driven_firm_engine.AIDrivenFirmDecisionEngine'):

            result = self.firm_system.spawn_firm(self.mock_simulation, household)
            self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
