
import pytest
from unittest.mock import Mock, MagicMock
import math
from simulation.firms import Firm
from simulation.components.production_department import ProductionDepartment
from simulation.components.sales_department import SalesDepartment

class TestFirmBookValue:
    @pytest.fixture
    def mock_decision_engine(self):
        return Mock()

    @pytest.fixture
    def mock_config(self):
        config = Mock()
        config.FIRM_MIN_PRODUCTION_TARGET = 10.0
        config.IPO_INITIAL_SHARES = 100.0
        config.PROFIT_HISTORY_TICKS = 10
        config.INITIAL_FIRM_LIQUIDITY_NEED = 100.0
        config.LABOR_ALPHA = 0.7
        config.CAPITAL_DEPRECIATION_RATE = 0.05
        config.GOODS = {"test": {}}
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
        # Assets 1000, Shares 100, Treasury 100
        firm.treasury_shares = 0
        assert firm.finance.get_book_value_per_share() == 10.0

    def test_book_value_with_liabilities(self, firm, mock_decision_engine):
        # Setup Liabilities
        mock_loan_market = Mock()
        mock_bank = Mock()

        mock_decision_engine.loan_market = mock_loan_market
        mock_loan_market.bank = mock_bank
        firm.treasury_shares = 0

        # Mock both legacy and new interface to be safe
        mock_bank.get_debt_summary.return_value = {"total_principal": 200.0}
        mock_bank.get_debt_status.return_value = {"total_outstanding_debt": 200.0}

        # Net Assets = 1000 - 200 = 800. Shares 100.
        assert firm.finance.get_book_value_per_share() == 8.0

    def test_book_value_with_treasury_shares(self, firm):
        firm.treasury_shares = 20.0
        # Assets 1000. Outstanding Shares 80.
        assert firm.finance.get_book_value_per_share() == 12.5

    def test_book_value_negative_net_assets(self, firm, mock_decision_engine):
         # Setup Huge Liabilities
        mock_loan_market = Mock()
        mock_bank = Mock()
        mock_decision_engine.loan_market = mock_loan_market
        mock_loan_market.bank = mock_bank
        firm.treasury_shares = 0

        # Mock both legacy and new interface
        mock_bank.get_debt_summary.return_value = {"total_principal": 2000.0}
        mock_bank.get_debt_status.return_value = {"total_outstanding_debt": 2000.0}

        # Net Assets = 1000 - 2000 = -1000.
        # Should return 0.0
        assert firm.finance.get_book_value_per_share() == 0.0

    def test_book_value_zero_shares(self, firm):
        firm.total_shares = 0.0
        firm.treasury_shares = 0.0
        assert firm.finance.get_book_value_per_share() == 0.0

class TestProductionDepartment:
    @pytest.fixture
    def mock_config(self):
        config = Mock()
        config.LABOR_ALPHA = 0.7
        config.AUTOMATION_LABOR_REDUCTION = 0.5
        config.LABOR_ELASTICITY_MIN = 0.3
        config.CAPITAL_DEPRECIATION_RATE = 0.05
        config.GOODS = {"test": {"quality_sensitivity": 0.5}}
        return config

    @pytest.fixture
    def firm(self, mock_config):
        firm = Mock(spec=Firm)
        firm.id = 1
        firm.hr = Mock()
        firm.hr.employees = [Mock()] * 5
        firm.capital_stock = 100.0
        firm.automation_level = 0.0
        firm.productivity_factor = 1.0
        firm.specialization = "test"
        firm.input_inventory = {}
        firm.inventory = {}
        firm.inventory_quality = {}
        firm.base_quality = 1.0
        firm.hr.get_total_labor_skill.return_value = 5.0
        firm.hr.get_avg_skill.return_value = 1.0
        return firm

    def test_produce(self, firm, mock_config):
        prod_dept = ProductionDepartment(firm, mock_config)
        produced_quantity = prod_dept.produce(0)

        assert produced_quantity > 0
        assert firm.capital_stock < 100.0

        # Replicate the quality calculation to get the expected value
        avg_skill = firm.hr.get_avg_skill.return_value
        quality_sensitivity = mock_config.GOODS["test"]["quality_sensitivity"]
        expected_quality = firm.base_quality + (math.log1p(avg_skill) * quality_sensitivity)

        firm.add_inventory.assert_called_once_with("test", produced_quantity, expected_quality)

class TestSalesDepartment:
    @pytest.fixture
    def mock_config(self):
        config = Mock()
        config.BRAND_AWARENESS_SATURATION = 0.9
        config.MARKETING_EFFICIENCY_HIGH_THRESHOLD = 1.5
        config.MARKETING_EFFICIENCY_LOW_THRESHOLD = 0.8
        config.MARKETING_BUDGET_RATE_MIN = 0.01
        config.MARKETING_BUDGET_RATE_MAX = 0.20
        return config

    @pytest.fixture
    def firm(self, mock_config):
        firm = Mock(spec=Firm)
        firm.id = 1
        firm.brand_manager = Mock()
        firm.finance = Mock()
        firm.brand_manager.brand_awareness = 0.5
        firm.inventory_quality = {}
        firm.marketing_budget = 100.0
        firm.finance.last_marketing_spend = 50.0 # Lower spend last tick
        firm.finance.revenue_this_turn = 200.0
        firm.finance.last_revenue = 100.0
        firm.marketing_budget_rate = 0.1
        firm.logger = Mock()
        return firm

    def test_post_ask(self, firm, mock_config):
        sales_dept = SalesDepartment(firm, mock_config)
        market = Mock()
        order = sales_dept.post_ask("test", 10.0, 5.0, market, 0)

        market.place_order.assert_called_once()
        assert order.agent_id == firm.id
        assert order.item_id == "test"

    def test_adjust_marketing_budget_increase(self, firm, mock_config):
        # High ROI should increase the budget rate
        firm.finance.last_marketing_spend = 50.0
        firm.finance.revenue_this_turn = 200.0
        firm.finance.last_revenue = 100.0

        sales_dept = SalesDepartment(firm, mock_config)
        initial_rate = firm.marketing_budget_rate
        sales_dept.adjust_marketing_budget()

        assert firm.marketing_budget_rate > initial_rate

    def test_adjust_marketing_budget_decrease(self, firm, mock_config):
        # Low ROI should decrease the budget rate
        firm.finance.last_marketing_spend = 200.0 # High spend
        firm.finance.revenue_this_turn = 110.0 # Low return
        firm.finance.last_revenue = 100.0

        sales_dept = SalesDepartment(firm, mock_config)
        initial_rate = firm.marketing_budget_rate
        sales_dept.adjust_marketing_budget()

        assert firm.marketing_budget_rate < initial_rate
