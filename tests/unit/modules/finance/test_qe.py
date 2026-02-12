import pytest
from unittest.mock import MagicMock, ANY
from modules.finance.system import FinanceSystem
from modules.simulation.api import AgentStateDTO
from modules.system.api import DEFAULT_CURRENCY

class TestQE:
    def test_issue_treasury_bonds_qe_trigger(self):
        # 1. Setup
        mock_gov = MagicMock()
        mock_cb = MagicMock()
        mock_bank = MagicMock()
        mock_config = MagicMock()
        mock_settlement = MagicMock()

        mock_bank.id = 100
        mock_cb.id = 999

        fs = FinanceSystem(mock_gov, mock_cb, mock_bank, mock_config, mock_settlement)

        # Configure QE Trigger
        mock_config.get.return_value = 1.5 # Threshold
        mock_gov.sensory_data.current_gdp = 100.0
        mock_gov.total_debt = 200.0 # Ratio = 2.0 > 1.5

        # Mock Settlement Balance (for sync_ledger_balances)
        mock_settlement.get_balance.return_value = 5000 # Enough funds

        # 2. Execute
        fs.issue_treasury_bonds(1000, 1)

        # 3. Verify
        mock_settlement.transfer.assert_called_with(
            mock_cb, # Buyer should be Central Bank
            mock_gov,
            1000,
            memo=ANY,
            currency=DEFAULT_CURRENCY
        )

    def test_issue_treasury_bonds_normal(self):
        # 1. Setup
        mock_gov = MagicMock()
        mock_cb = MagicMock()
        mock_bank = MagicMock()
        mock_config = MagicMock()
        mock_settlement = MagicMock()

        mock_bank.id = 100
        mock_cb.id = 999

        fs = FinanceSystem(mock_gov, mock_cb, mock_bank, mock_config, mock_settlement)

        # Configure Normal
        mock_config.get.return_value = 1.5
        mock_gov.sensory_data.current_gdp = 100.0
        mock_gov.total_debt = 100.0 # Ratio = 1.0 < 1.5

        # Mock Settlement Balance (for sync_ledger_balances)
        mock_settlement.get_balance.return_value = 5000 # Enough funds

        # 2. Execute
        fs.issue_treasury_bonds(1000, 1)

        # 3. Verify
        mock_settlement.transfer.assert_called_with(
            mock_bank, # Buyer should be Bank
            mock_gov,
            1000,
            memo=ANY,
            currency=DEFAULT_CURRENCY
        )
