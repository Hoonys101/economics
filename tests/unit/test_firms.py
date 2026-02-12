import pytest
from unittest.mock import Mock, MagicMock
import math
from simulation.firms import Firm
from modules.system.api import DEFAULT_CURRENCY
from simulation.components.state.firm_state_models import FinanceState, SalesState
from tests.utils.factories import create_firm, create_firm_config_dto

class TestFirmBookValue:
    @pytest.fixture
    def mock_decision_engine(self):
        return Mock()

    @pytest.fixture
    def mock_config(self):
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
        return create_firm(
            id=1,
            name="Firm_1",
            engine=mock_decision_engine,
            specialization="test",
            productivity_factor=1.0,
            config_dto=mock_config,
            sector="FOOD",
            assets=0
        )

    def test_book_value_no_liabilities(self, firm):
        # Assets 1000 pennies ($10.00)
        firm.wallet.add(1000, DEFAULT_CURRENCY)
        firm.finance_state.total_shares = 100.0
        firm.finance_state.treasury_shares = 0.0

        # Net Assets = 1000 - 0 = 1000. Shares 100.
        # BV/Share = 10.0 pennies/share
        result = firm.get_book_value_per_share()
        assert result == 10.0

    def test_book_value_with_liabilities(self, firm):
        firm.wallet.add(1000, DEFAULT_CURRENCY)
        firm.finance_state.total_shares = 100.0
        firm.finance_state.treasury_shares = 0.0

        # Liabilities 200 pennies
        firm.finance_state.total_debt_pennies = 200

        # Net Assets = 1000 - 200 = 800. Shares 100.
        result = firm.get_book_value_per_share()
        assert result == 8.0

    def test_book_value_with_treasury_shares(self, firm):
        firm.wallet.add(1000, DEFAULT_CURRENCY)
        firm.finance_state.total_shares = 100.0
        firm.finance_state.treasury_shares = 20.0

        # Assets 1000. Outstanding Shares 80.
        result = firm.get_book_value_per_share()
        assert result == 12.5

    def test_book_value_negative_net_assets(self, firm):
        firm.wallet.add(1000, DEFAULT_CURRENCY)
        firm.finance_state.total_shares = 100.0
        firm.finance_state.treasury_shares = 0.0
        firm.finance_state.total_debt_pennies = 2000

        # Net Assets = 1000 - 2000 = -1000.
        # Should return 0.0
        result = firm.get_book_value_per_share()
        assert result == 0.0

    def test_book_value_zero_shares(self, firm):
        firm.finance_state.total_shares = 0.0
        firm.finance_state.treasury_shares = 0.0
        result = firm.get_book_value_per_share()
        assert result == 0.0

class TestFirmProduction:
    @pytest.fixture
    def mock_config(self):
        dto = create_firm_config_dto()
        dto.labor_alpha = 0.7
        dto.automation_labor_reduction = 0.5
        dto.labor_elasticity_min = 0.3
        dto.capital_depreciation_rate = 0.05
        dto.goods = {"test": {"quality_sensitivity": 0.5}}
        return dto

    @pytest.fixture
    def firm(self, mock_config):
        firm = create_firm(
            id=1,
            name="Firm_1",
            engine=Mock(),
            specialization="test",
            productivity_factor=1.0,
            config_dto=mock_config,
            sector="FOOD",
            assets=0
        )
        # Setup Production State
        firm.production_state.capital_stock = 100.0
        firm.production_state.automation_level = 0.0
        firm.production_state.productivity_factor = 1.0
        firm.production_state.base_quality = 1.0

        # Setup HR State (Need employees)
        mock_emp = Mock()
        mock_emp.labor_skill = 1.0
        firm.hr_state.employees = [mock_emp] * 5

        return firm

    def test_produce(self, firm, mock_config):
        # Initial checks
        assert firm.production_state.capital_stock == 100.0

        # Run production
        firm.produce(current_time=0)

        produced_quantity = firm.get_quantity("test")

        assert produced_quantity > 0
        assert firm.production_state.capital_stock < 100.0 # Depreciation applied

        # Quality check
        avg_skill = 1.0
        quality_sensitivity = mock_config.goods["test"]["quality_sensitivity"]
        expected_quality = 1.0 + (math.log1p(avg_skill) * quality_sensitivity)

        actual_quality = firm.get_quality("test")
        assert abs(actual_quality - expected_quality) < 0.001

class TestFirmSales:
    @pytest.fixture
    def mock_config(self):
        dto = create_firm_config_dto()
        dto.brand_awareness_saturation = 0.9
        dto.marketing_efficiency_high_threshold = 1.5
        dto.marketing_efficiency_low_threshold = 0.8
        dto.marketing_budget_rate_min = 0.01
        dto.marketing_budget_rate_max = 0.20
        return dto

    @pytest.fixture
    def firm(self, mock_config):
        firm = create_firm(
            id=1,
            name="Firm_1",
            engine=Mock(),
            specialization="test",
            productivity_factor=1.0,
            config_dto=mock_config,
            initial_inventory={"test": 100.0},
            sector="FOOD",
            assets=0
        )
        firm.sales_state.brand_awareness = 0.5
        firm.sales_state.perceived_quality = 1.0

        firm.sales_state.marketing_budget_pennies = 100 # 100 pennies
        firm.sales_state.marketing_budget_rate = 0.1

        firm.finance_state.last_marketing_spend_pennies = 50
        firm.finance_state.revenue_this_turn = {DEFAULT_CURRENCY: 200}
        firm.finance_state.last_revenue_pennies = 100

        return firm

    def test_post_ask(self, firm, mock_config):
        market = Mock()
        market.id = "test_market"

        order = firm.post_ask("test", 10.0, 5.0, market, 0)

        assert order.agent_id == firm.id
        assert order.item_id == "test"
        assert order.quantity == 5.0
        # Check brand injection
        assert order.brand_info is not None
        assert order.brand_info['brand_awareness'] == 0.5

    def test_adjust_marketing_budget_increase(self, firm, mock_config):
        # High ROI should increase the budget rate
        # Using _adjust_marketing_budget helper which calls SalesEngine

        firm.finance_state.last_marketing_spend_pennies = 50
        firm.finance_state.revenue_this_turn = {DEFAULT_CURRENCY: 200} # pennies
        firm.finance_state.last_revenue_pennies = 100 # pennies

        # Need context with exchange rates
        context = {"exchange_rates": {DEFAULT_CURRENCY: 1.0}}

        firm._adjust_marketing_budget(context)

        # Revenue = 200. Rate = 0.1. Target = 20.
        # Old Budget = 100.
        # New Budget = 100 * 0.8 + 20 * 0.2 = 80 + 4 = 84.

        assert firm.sales_state.marketing_budget_pennies == 84
