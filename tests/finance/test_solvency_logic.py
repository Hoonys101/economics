import pytest
from unittest.mock import MagicMock, Mock, create_autospec
from modules.finance.system import FinanceSystem
from modules.finance.api import IFinancialFirm
from simulation.firms import Firm
from modules.simulation.api import AgentCoreConfigDTO
from modules.simulation.dtos.api import FirmConfigDTO

class TestSolvencyLogic:
    @pytest.fixture
    def mock_firm(self):
        """Creates a mock firm adhering to IFinancialFirm protocol."""
        mock_firm = create_autospec(IFinancialFirm, instance=True)
        return mock_firm

    @pytest.fixture
    def finance_system(self, mock_config):
        # We need a finance system with mocked dependencies
        mock_gov = Mock()
        mock_cb = Mock()
        mock_bank = Mock()

        # Ensure mock_config has .get() method as FinanceSystem uses it
        mock_config.get = Mock(side_effect=lambda key, default=None: default)

        # Override specific config values for testing
        def config_get(key, default=None):
            if key == "economy_params.STARTUP_GRACE_PERIOD_TICKS":
                return 24
            if key == "economy_params.ALTMAN_Z_SCORE_THRESHOLD":
                return 1.81
            return default
        mock_config.get.side_effect = config_get

        fs = FinanceSystem(mock_gov, mock_cb, mock_bank, mock_config)
        return fs

    def test_solvency_grace_period_solvent(self, finance_system, mock_firm):
        """Test solvency check during grace period (solvent)."""
        mock_firm.age = 10
        mock_firm.monthly_wage_bill_pennies = 1000  # 10.00
        mock_firm.balance_pennies = 3000        # 30.00 (Runway = 3 months)

        # Should be solvent (Assets >= 3 * Monthly Wages)
        assert finance_system.evaluate_solvency(mock_firm, current_tick=10) is True

    def test_solvency_grace_period_insolvent(self, finance_system, mock_firm):
        """Test solvency check during grace period (insolvent)."""
        mock_firm.age = 10
        mock_firm.monthly_wage_bill_pennies = 1000
        mock_firm.balance_pennies = 2999        # < 3000

        assert finance_system.evaluate_solvency(mock_firm, current_tick=10) is False

    def test_solvency_established_firm(self, finance_system, mock_firm):
        """Test solvency check for established firm using Z-Score."""
        mock_firm.age = 100

        # Set up financial data for Z-Score calculation
        mock_firm.balance_pennies = 10000      # Cash
        mock_firm.inventory_value_pennies = 5000
        mock_firm.capital_stock_pennies = 20000
        mock_firm.total_debt_pennies = 8000
        mock_firm.retained_earnings_pennies = 2000
        mock_firm.average_profit_pennies = 1000

        # Verify it runs without error and returns a bool
        result = finance_system.evaluate_solvency(mock_firm, current_tick=100)
        assert isinstance(result, bool)

    def test_firm_implementation(self):
        """Verify Firm class implements IFinancialFirm correctly."""
        print(f"Firm MRO: {Firm.mro()}")
        if hasattr(Firm, 'age'):
            print(f"Firm.age: {Firm.age}")
        else:
            print("Firm has no class attribute 'age'")

        core_config = AgentCoreConfigDTO(
            id=1, name="TestFirm", logger=Mock(), memory_interface=Mock(),
            value_orientation="PROFIT", initial_needs={}
        )

        config_dto = Mock(spec=FirmConfigDTO)
        config_dto.firm_min_production_target = 10.0
        config_dto.ipo_initial_shares = 100.0
        config_dto.dividend_rate = 0.1
        config_dto.profit_history_ticks = 10
        config_dto.goods = {}
        config_dto.fire_sale_discount = 0.5

        firm = Firm(
            core_config=core_config,
            engine=Mock(),
            specialization="FOOD",
            productivity_factor=1.0,
            config_dto=config_dto
        )

        # Check instance against protocol
        assert isinstance(firm, IFinancialFirm)

        # Check properties return int
        # Default initialization values
        assert isinstance(firm.capital_stock_pennies, int)
        assert firm.capital_stock_pennies == firm.production_state.capital_stock

        assert isinstance(firm.inventory_value_pennies, int)
        assert firm.inventory_value_pennies == 0 # No inventory

        assert isinstance(firm.monthly_wage_bill_pennies, int)
        assert firm.monthly_wage_bill_pennies == 0 # No employees

        assert isinstance(firm.total_debt_pennies, int)
        assert firm.total_debt_pennies == 0

        assert isinstance(firm.retained_earnings_pennies, int)
        assert firm.retained_earnings_pennies == 0

        assert isinstance(firm.average_profit_pennies, int)
        assert firm.average_profit_pennies == 0

        assert isinstance(firm.age, int)
