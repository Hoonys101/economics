import pytest
from unittest.mock import MagicMock, patch
from simulation.components.finance_department import FinanceDepartment
from simulation.dtos.financial_dtos import FinancialStatementDTO

class TestFinanceDepartmentSolvency:

    @pytest.fixture
    def mock_firm(self):
        firm = MagicMock()
        firm.assets = 1000.0
        firm.capital_stock = 500.0
        firm.inventory = {}
        firm.total_debt = 200.0
        firm.last_prices = {}
        return firm

    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        config.PROFIT_HISTORY_TICKS = 10
        config.GOODS = {}
        return config

    @pytest.fixture
    def finance_dept(self, mock_firm, mock_config):
        dept = FinanceDepartment(mock_firm, mock_config)
        return dept

    def test_get_financial_snapshot_structure(self, finance_dept, mock_firm):
        # Setup
        mock_firm.assets = 1000.0
        mock_firm.capital_stock = 500.0
        mock_firm.inventory = {"apple": 10}
        mock_firm.last_prices = {"apple": 5.0}
        # Inventory Value = 10 * 5 = 50.0
        # Total Assets = 1000 + 50 + 500 = 1550.0
        # Current Assets = 1000 + 50 = 1050.0
        # Total Debt = 200.0
        # Working Capital = 1050 - 200 = 850.0

        finance_dept.retained_earnings = 300.0
        finance_dept.current_profit = 100.0

        snapshot = finance_dept.get_financial_snapshot()

        assert snapshot["total_assets"] == 1550.0
        assert snapshot["working_capital"] == 850.0
        assert snapshot["retained_earnings"] == 300.0
        assert snapshot["average_profit"] == 100.0
        assert snapshot["total_debt"] == 200.0

    def test_get_altman_z_score_delegation(self, finance_dept, mock_firm):
        # Setup specific values
        mock_firm.assets = 1000.0
        mock_firm.capital_stock = 0.0
        mock_firm.inventory = {}
        mock_firm.total_debt = 0.0

        # Mock the calculator
        mock_calculator = MagicMock()
        mock_calculator.calculate.return_value = 99.9
        finance_dept.solvency_calculator = mock_calculator

        # Execute
        result = finance_dept.get_altman_z_score()

        # Verify
        assert result == 99.9
        mock_calculator.calculate.assert_called_once()

        # Check arguments passed to calculate
        call_args = mock_calculator.calculate.call_args[0][0]
        assert isinstance(call_args, dict) # TypedDict is a dict at runtime
        assert "total_assets" in call_args
        assert "working_capital" in call_args
