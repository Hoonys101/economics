import pytest
from unittest.mock import Mock, patch
from simulation.components.finance_department import FinanceDepartment
from simulation.firms import Firm
from simulation.dtos.financial_dtos import FinancialStatementDTO

class TestFinanceDepartment:
    @pytest.fixture
    def mock_firm(self):
        firm = Mock(spec=Firm)
        firm.id = 1
        firm.assets = 1000.0
        firm.capital_stock = 200.0
        firm.inventory = {}
        firm.last_prices = {}
        firm.total_debt = 500.0
        firm.logger = Mock()
        return firm

    @pytest.fixture
    def config_module(self):
        config = Mock()
        config.PROFIT_HISTORY_TICKS = 10
        return config

    @pytest.fixture
    def finance_dept(self, mock_firm, config_module):
        return FinanceDepartment(mock_firm, config_module)

    def test_get_altman_z_score_delegation(self, finance_dept):
        """Test that get_altman_z_score correctly assembles DTO and delegates to calculator."""

        # Setup specific financial state
        finance_dept.firm.assets = 500.0 # Cash
        # Inventory value defaults to 0 as inventory is empty
        finance_dept.firm.total_debt = 200.0
        finance_dept.retained_earnings = 150.0
        finance_dept.current_profit = 50.0
        finance_dept.profit_history.append(50.0)

        # Expected values for DTO
        # Total Assets = Cash (500) + Inventory (0) = 500
        # Working Capital = Total Assets (500) - Debt (200) = 300
        # Retained Earnings = 150
        # Avg Profit = 50
        # Total Debt = 200

        expected_dto = FinancialStatementDTO(
            total_assets=500.0,
            working_capital=300.0,
            retained_earnings=150.0,
            average_profit=50.0,
            total_debt=200.0
        )

        # Mock the calculator within finance_dept
        with patch.object(finance_dept.solvency_calculator, 'calculate', return_value=1.23) as mock_calculate:
            result = finance_dept.get_altman_z_score()

            assert result == 1.23
            mock_calculate.assert_called_once()
            call_arg = mock_calculate.call_args[0][0]

            # Assert DTO content matches
            assert call_arg == expected_dto

    def test_get_altman_z_score_integration(self, finance_dept):
        """Test integration with real calculator (using default logic)."""
        finance_dept.firm.assets = 1000.0
        finance_dept.firm.total_debt = 400.0 # WC = 600
        finance_dept.retained_earnings = 200.0
        finance_dept.current_profit = 100.0
        finance_dept.profit_history.append(100.0)

        # X1 = 600/1000 = 0.6
        # X2 = 200/1000 = 0.2
        # X3 = 100/1000 = 0.1
        # Z = 1.2*0.6 + 1.4*0.2 + 3.3*0.1 = 0.72 + 0.28 + 0.33 = 1.33

        z_score = finance_dept.get_altman_z_score()
        assert z_score == pytest.approx(1.33, 0.001)
