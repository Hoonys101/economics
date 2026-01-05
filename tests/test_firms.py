
import pytest
from unittest.mock import Mock, MagicMock
from simulation.firms import Firm

class TestFirmBookValue:
    @pytest.fixture
    def mock_decision_engine(self):
        return Mock()

    @pytest.fixture
    def mock_config(self):
        config = Mock()
        config.FIRM_MIN_PRODUCTION_TARGET = 10.0
        config.FIRM_DEFAULT_TOTAL_SHARES = 100.0
        config.PROFIT_HISTORY_TICKS = 10
        config.INITIAL_FIRM_LIQUIDITY_NEED = 100.0
        return config

    @pytest.fixture
    def firm(self, mock_decision_engine, mock_config):
        return Firm(
            id=1,
            initial_capital=1000.0,
            initial_liquidity_need=100.0,
            specialization="test",
            productivity_factor=1.0,
            decision_engine=mock_decision_engine,
            value_orientation="PROFIT",
            config_module=mock_config
        )

    def test_book_value_no_liabilities(self, firm):
        # Assets 1000, Shares 100, Treasury 0
        assert firm.get_book_value_per_share() == 10.0

    def test_book_value_with_liabilities(self, firm, mock_decision_engine):
        # Setup Liabilities
        mock_loan_market = Mock()
        mock_bank = Mock()

        mock_decision_engine.loan_market = mock_loan_market
        mock_loan_market.bank = mock_bank

        mock_bank.get_debt_summary.return_value = {"total_principal": 200.0}

        # Net Assets = 1000 - 200 = 800. Shares 100.
        assert firm.get_book_value_per_share() == 8.0

    def test_book_value_with_treasury_shares(self, firm):
        firm.treasury_shares = 20.0
        # Assets 1000. Outstanding Shares 80.
        assert firm.get_book_value_per_share() == 12.5

    def test_book_value_negative_net_assets(self, firm, mock_decision_engine):
         # Setup Huge Liabilities
        mock_loan_market = Mock()
        mock_bank = Mock()
        mock_decision_engine.loan_market = mock_loan_market
        mock_loan_market.bank = mock_bank

        mock_bank.get_debt_summary.return_value = {"total_principal": 2000.0}

        # Net Assets = 1000 - 2000 = -1000.
        # Should return 0.0
        assert firm.get_book_value_per_share() == 0.0

    def test_book_value_zero_shares(self, firm):
        firm.total_shares = 0.0
        assert firm.get_book_value_per_share() == 0.0
