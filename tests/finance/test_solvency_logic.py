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
        mock_firm.id = "FIRM_1"
        finance_system.settlement_system = MagicMock()
        finance_system.settlement_system.get_balance.return_value = 3000

        from modules.finance.api import FirmFinancialSnapshotDTO
        snapshot = FirmFinancialSnapshotDTO(
            firm_id=mock_firm.id,
            age=10,
            monthly_wage_bill_pennies=1000,
            inventory_value_pennies=0,
            capital_stock_units=0.0,
            retained_earnings_pennies=0,
            average_profit_pennies=0,
            total_debt_pennies=0
        )

        # Should be solvent (Assets >= 3 * Monthly Wages)
        report = finance_system.evaluate_solvency(snapshot, current_tick=10)
        assert report.is_solvent is True

    def test_solvency_grace_period_insolvent(self, finance_system, mock_firm):
        """Test solvency check during grace period (insolvent)."""
        mock_firm.id = "FIRM_1"
        finance_system.settlement_system = MagicMock()
        finance_system.settlement_system.get_balance.return_value = 2999

        from modules.finance.api import FirmFinancialSnapshotDTO
        snapshot = FirmFinancialSnapshotDTO(
            firm_id=mock_firm.id,
            age=10,
            monthly_wage_bill_pennies=1000,
            inventory_value_pennies=0,
            capital_stock_units=0.0,
            retained_earnings_pennies=0,
            average_profit_pennies=0,
            total_debt_pennies=0
        )

        report = finance_system.evaluate_solvency(snapshot, current_tick=10)
        assert report.is_solvent is False

    def test_solvency_established_firm(self, finance_system, mock_firm):
        """Test solvency check for established firm using Z-Score."""
        mock_firm.id = "FIRM_1"
        finance_system.settlement_system = MagicMock()
        finance_system.settlement_system.get_balance.return_value = 10000

        from modules.finance.api import FirmFinancialSnapshotDTO
        snapshot = FirmFinancialSnapshotDTO(
            firm_id=mock_firm.id,
            age=100,
            monthly_wage_bill_pennies=1000,
            inventory_value_pennies=5000,
            capital_stock_units=200.0,
            retained_earnings_pennies=2000,
            average_profit_pennies=1000,
            total_debt_pennies=8000
        )

        # Verify it runs without error and returns a SolvencyReportDTO
        result = finance_system.evaluate_solvency(snapshot, current_tick=100)
        assert hasattr(result, "is_solvent")

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
            specialization="FOOD_PROD",
            productivity_factor=1.0,
            config_dto=config_dto
        )

        # Check instance against protocol
        assert isinstance(firm, IFinancialFirm)

        # Check properties return int
        # Default initialization values
        assert isinstance(firm.capital_stock_units, int)
        assert firm.capital_stock_units == firm.production_state.capital_stock

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

    def test_evaluate_solvency_ssot_balance(self, finance_system, mock_firm):
        """Verify that evaluate_solvency uses ISettlementSystem.get_balance exclusively."""
        from modules.finance.api import FirmFinancialSnapshotDTO

        mock_firm.id = "FIRM_SSOT"
        finance_system.settlement_system = MagicMock()
        finance_system.settlement_system.get_balance.return_value = 5000

        snapshot = FirmFinancialSnapshotDTO(
            firm_id=mock_firm.id,
            age=100,
            monthly_wage_bill_pennies=1000,
            inventory_value_pennies=1000,
            capital_stock_units=50.0,
            retained_earnings_pennies=500,
            average_profit_pennies=200,
            total_debt_pennies=1000
        )

        report = finance_system.evaluate_solvency(snapshot, current_tick=100)

        # Verify get_balance was called with the correct firm_id
        finance_system.settlement_system.get_balance.assert_called_once_with("FIRM_SSOT")

        # Total assets should be SSoT Balance (5000) + Inventory (1000) + Capital Stock (50 * 100 = 5000) = 11000
        assert report.total_assets_pennies == 11000

        # Working Capital should be (SSoT Balance (5000) + Inventory (1000)) - Debt (1000) = 5000
        assert report.working_capital_pennies == 5000
