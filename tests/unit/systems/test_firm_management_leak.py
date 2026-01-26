import unittest
from unittest.mock import Mock, MagicMock, patch
import simulation.firms
import simulation.ai.firm_ai
import simulation.decisions.ai_driven_firm_engine
from simulation.systems.firm_management import FirmSystem

class TestFirmManagementLeak(unittest.TestCase):
    def setUp(self):
        self.mock_config = Mock()
        self.mock_config.STARTUP_COST = 1000.0
        self.mock_config.VISIONARY_MUTATION_RATE = 0.0
        self.mock_config.VALUE_ORIENTATION_WEALTH_AND_NEEDS = "WEALTH_AND_NEEDS"
        self.mock_config.VALUE_ORIENTATION_NEEDS_AND_GROWTH = "NEEDS_AND_GROWTH"
        self.mock_config.GOODS = {
            "food": {"sector": "PRIMARY", "inputs": {}},
            "steel": {"sector": "SECONDARY", "inputs": {"iron": 1.0}} # Has inputs!
        }
        self.mock_config.SERVICE_SECTORS = []
        self.mock_config.INITIAL_FIRM_LIQUIDITY_NEED_MEAN = 50.0
        self.mock_config.FIRM_MIN_PRODUCTION_TARGET = 10.0
        self.mock_config.PROFIT_HISTORY_TICKS = 10
        self.mock_config.INVENTORY_HOLDING_COST_RATE = 0.01
        self.mock_config.STARTUP_CAPITAL_MULTIPLIER = 1.5

        self.firm_system = FirmSystem(self.mock_config)

        self.mock_simulation = MagicMock()
        self.mock_simulation.agents = {}
        self.mock_simulation.firms = []
        self.mock_simulation.households = []
        self.mock_simulation.markets = {}
        self.mock_simulation.stock_market = MagicMock()
        self.mock_simulation.ai_training_manager = MagicMock()
        self.mock_simulation.logger = MagicMock()
        self.mock_simulation.settlement_system = MagicMock()
        self.mock_simulation.settlement_system.transfer.return_value = True

    def test_spawn_firm_leak_detection(self):
        """
        Verify that startup_cost is calculated correctly and transferred via SettlementSystem.
        """
        # 1. Setup Household
        household = MagicMock()
        household.id = 1
        household.assets = 5000.0
        household._sub_assets = MagicMock()

        # 2. Patch dependencies
        with patch('simulation.systems.firm_management.random.choice', return_value='steel'), \
             patch('simulation.systems.firm_management.random.random', return_value=0.9), \
             patch('simulation.firms.Firm') as MockFirm, \
             patch('simulation.ai.firm_ai.FirmAI'), \
             patch('simulation.ai.service_firm_ai.ServiceFirmAI'), \
             patch('simulation.decisions.ai_driven_firm_engine.AIDrivenFirmDecisionEngine'):

            # Mock Firm instance
            mock_firm_instance = MockFirm.return_value
            mock_firm_instance.id = 101
            # Mock _add_assets for legacy fallback check (should not be called if settlement_system exists)
            mock_firm_instance._add_assets = MagicMock()

            # 3. Run spawn_firm
            self.firm_system.spawn_firm(self.mock_simulation, household)

            # 4. Check Settlement System Usage
            # Expected Cost: 1000 * 1.5 = 1500.0
            expected_cost = 1500.0

            self.mock_simulation.settlement_system.transfer.assert_called_once()
            args = self.mock_simulation.settlement_system.transfer.call_args[0]
            # args: (founder, new_firm, amount, memo)
            self.assertEqual(args[0], household)
            # args[1] is the new firm instance (mock_firm_instance)
            self.assertEqual(args[2], expected_cost)

            # 5. Check Firm Initial Capital passed to constructor
            # Should be 0.0
            call_kwargs = MockFirm.call_args[1]
            firm_initial_capital = call_kwargs.get('initial_capital')
            self.assertEqual(firm_initial_capital, 0.0)

            # 6. Check that direct _sub_assets was NOT called on household (since transfer handles it)
            # Wait, SettlementSystem.transfer calls withdraw/deposit.
            # My mock SettlementSystem.transfer does nothing but return True.
            # So household._sub_assets should NOT be called directly by spawn_firm.
            # And firm._add_assets should NOT be called directly.

            household._sub_assets.assert_not_called()
            mock_firm_instance._add_assets.assert_not_called()

            print("Firm Spawn Leak Test: SUCCESS (Transferred 1500.0 correctly, Initial Capital 0)")

if __name__ == '__main__':
    unittest.main()
