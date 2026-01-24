import unittest
from unittest.mock import Mock, MagicMock, patch
from simulation.systems.ma_manager import MAManager

class TestMAManager(unittest.TestCase):
    def setUp(self):
        self.mock_simulation = MagicMock()
        self.mock_config = Mock()
        self.mock_config.MA_ENABLED = True
        self.mock_config.BANKRUPTCY_CONSECUTIVE_LOSS_TICKS = 20
        self.mock_config.HOSTILE_TAKEOVER_DISCOUNT_THRESHOLD = 0.7
        self.mock_config.MIN_ACQUISITION_CASH_RATIO = 1.5

        # Mock simulation components
        self.mock_simulation.firms = []
        self.mock_simulation.agents = {}
        self.mock_simulation.government = MagicMock()

        # Initialize MAManager
        self.ma_manager = MAManager(self.mock_simulation, self.mock_config)

    def test_execute_bankruptcy_records_loss_in_ledger(self):
        """
        Verify that _execute_bankruptcy calls settlement_system.record_liquidation_loss.
        """
        # 1. Setup Firm
        mock_firm = MagicMock()
        mock_firm.id = 999
        mock_firm.is_active = True
        mock_firm.hr.employees = []

        # Mock liquidate_assets to return a specific amount
        recovered_cash = 1000.0
        mock_firm.liquidate_assets.return_value = recovered_cash

        # 2. Setup SettlementSystem
        mock_settlement_system = MagicMock()
        self.mock_simulation.settlement_system = mock_settlement_system

        # 3. Execute
        current_tick = 123
        self.ma_manager._execute_bankruptcy(mock_firm, current_tick)

        # 4. Assert
        # Assert liquidation was called
        mock_firm.liquidate_assets.assert_called_once()

        # Assert loss was recorded in ledger
        mock_settlement_system.record_liquidation_loss.assert_called_once_with(
            firm=mock_firm,
            amount=recovered_cash,
            tick=current_tick
        )

        # Assert firm deactivated
        self.assertFalse(mock_firm.is_active)

if __name__ == '__main__':
    unittest.main()
