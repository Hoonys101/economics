import pytest
from unittest.mock import Mock, MagicMock
import math
from simulation.firms import Firm
from simulation.components.production_department import ProductionDepartment
from simulation.components.sales_department import SalesDepartment
from modules.system.api import DEFAULT_CURRENCY

class TestFirmBookValue:
    @pytest.fixture
    def mock_decision_engine(self):
        return Mock()

    @pytest.fixture
    def mock_config(self):
        from tests.utils.factories import create_firm_config_dto

        dto = create_firm_config_dto()
        # Override specific fields if needed for tests
        dto.firm_min_production_target = 10.0
        dto.ipo_initial_shares = 100.0
        dto.profit_history_ticks = 10
        dto.initial_firm_liquidity_need = 100.0
        dto.labor_alpha = 0.7
        dto.capital_depreciation_rate = 0.05
        dto.goods = {"test": {"quality_sensitivity": 0.5}}
        dto.valuation_per_multiplier = 10.0 # Default if not set in factory
        return dto

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
            config_dto=mock_config
        )

    def test_book_value_no_liabilities(self, firm):
        # Assets 1000, Shares 100, Treasury 100
        firm.treasury_shares = 0
        # Accessing FinanceDepartment directly returns MoneyDTO
        result = firm.finance.get_book_value_per_share()
        assert result['amount'] == 10.0
        assert result['currency'] == DEFAULT_CURRENCY

    def test_book_value_with_liabilities(self, firm, mock_decision_engine):
        # Setup Liabilities
        firm.treasury_shares = 0

        # New FinanceDepartment uses firm.total_debt
        firm.total_debt = 200.0

        # Net Assets = 1000 - 200 = 800. Shares 100.
        result = firm.finance.get_book_value_per_share()
        assert result['amount'] == 8.0

    def test_book_value_with_treasury_shares(self, firm):
        firm.treasury_shares = 20.0
        # Assets 1000. Outstanding Shares 80.
        result = firm.finance.get_book_value_per_share()
        assert result['amount'] == 12.5

    def test_book_value_negative_net_assets(self, firm, mock_decision_engine):
         # Setup Huge Liabilities
        firm.treasury_shares = 0
        firm.total_debt = 2000.0

        # Net Assets = 1000 - 2000 = -1000.
        # Should return 0.0
        result = firm.finance.get_book_value_per_share()
        assert result['amount'] == 0.0

    def test_book_value_zero_shares(self, firm):
        firm.total_shares = 0.0
        firm.treasury_shares = 0.0
        result = firm.finance.get_book_value_per_share()
        assert result['amount'] == 0.0

class TestProductionDepartment:
    @pytest.fixture
    def mock_config(self):
        from tests.utils.factories import create_firm_config_dto

        dto = create_firm_config_dto()
        dto.labor_alpha = 0.7
        dto.automation_labor_reduction = 0.5
        dto.labor_elasticity_min = 0.3
        dto.capital_depreciation_rate = 0.05
        dto.goods = {"test": {"quality_sensitivity": 0.5}}
        return dto

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
        # Mock finance balance for produce() check
        firm.finance = Mock()
        firm.finance.balance = {DEFAULT_CURRENCY: 1000.0}
        firm.production_target = 100.0
        return firm

    def test_produce(self, firm, mock_config):
        prod_dept = ProductionDepartment(firm, mock_config)
        produced_quantity = prod_dept.produce(0)

        assert produced_quantity > 0
        assert firm.capital_stock < 100.0

        # Replicate the quality calculation to get the expected value
        avg_skill = firm.hr.get_avg_skill.return_value
        quality_sensitivity = mock_config.goods["test"]["quality_sensitivity"]
        expected_quality = firm.base_quality + (math.log1p(avg_skill) * quality_sensitivity)

        firm.add_inventory.assert_called_once_with("test", produced_quantity, expected_quality)

class TestSalesDepartment:
    @pytest.fixture
    def mock_config(self):
        from tests.utils.factories import create_firm_config_dto

        dto = create_firm_config_dto()
        dto.brand_awareness_saturation = 0.9
        dto.marketing_efficiency_high_threshold = 1.5
        dto.marketing_efficiency_low_threshold = 0.8
        dto.marketing_budget_rate_min = 0.01
        dto.marketing_budget_rate_max = 0.20
        return dto

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
        # Update: revenue_this_turn is a dict
        firm.finance.revenue_this_turn = {DEFAULT_CURRENCY: 200.0}
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

    def test_adjust_marketing_budget_increase(self, firm, mock_config, default_market_context):
        # High ROI should increase the budget rate
        firm.finance.last_marketing_spend = 50.0
        firm.finance.revenue_this_turn = {DEFAULT_CURRENCY: 200.0}
        firm.finance.last_revenue = 100.0
        # Mock convert_to_primary behavior on the mock object
        firm.finance.convert_to_primary.side_effect = lambda amt, cur, rates: amt

        sales_dept = SalesDepartment(firm, mock_config)
        initial_rate = firm.marketing_budget_rate
        sales_dept.adjust_marketing_budget(default_market_context)

        assert firm.marketing_budget_rate > initial_rate

    def test_adjust_marketing_budget_decrease(self, firm, mock_config, default_market_context):
        # Low ROI should decrease the budget rate
        firm.finance.last_marketing_spend = 200.0 # High spend
        firm.finance.revenue_this_turn = {DEFAULT_CURRENCY: 110.0} # Low return
        firm.finance.last_revenue = 100.0
        # Mock convert_to_primary behavior on the mock object
        firm.finance.convert_to_primary.side_effect = lambda amt, cur, rates: amt

        sales_dept = SalesDepartment(firm, mock_config)
        initial_rate = firm.marketing_budget_rate
        sales_dept.adjust_marketing_budget(default_market_context)

        assert firm.marketing_budget_rate < initial_rate
