import pytest
from unittest.mock import Mock, MagicMock, patch
from collections import deque

from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.firms import Firm
from simulation.schemas import FirmActionVector
from simulation.dtos import DecisionContext


# Mock Logger to prevent actual file writes during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch(
        "simulation.decisions.ai_driven_firm_engine.logging.getLogger"
    ) as mock_get_logger:
        mock_logger_instance = MagicMock(name="firm_decision_engine_logger")
        mock_get_logger.return_value = mock_logger_instance
        yield mock_logger_instance


# Mock config module for controlled testing
@pytest.fixture
def mock_config():
    mock_cfg = Mock()
    mock_cfg.OVERSTOCK_THRESHOLD = 1.2
    mock_cfg.UNDERSTOCK_THRESHOLD = 0.8
    mock_cfg.FIRM_MIN_PRODUCTION_TARGET = 10.0
    mock_cfg.FIRM_MAX_PRODUCTION_TARGET = 500.0
    mock_cfg.PRODUCTION_ADJUSTMENT_FACTOR = 0.1
    mock_cfg.FIRM_MIN_EMPLOYEES = 1
    mock_cfg.FIRM_MAX_EMPLOYEES = 50
    mock_cfg.BASE_WAGE = 10.0
    mock_cfg.GOODS = {
        "food": {"production_cost": 5.0}
    }
    mock_cfg.GOODS_MARKET_SELL_PRICE = 5.0
    mock_cfg.MIN_SELL_PRICE = 1.0
    mock_cfg.MAX_SELL_PRICE = 100.0
    mock_cfg.MAX_SELL_QUANTITY = 50.0
    mock_cfg.PRICE_ADJUSTMENT_FACTOR = 0.05
    mock_cfg.PRICE_ADJUSTMENT_EXPONENT = 1.2
    mock_cfg.AI_PRICE_ADJUSTMENT_SMALL = 0.05
    mock_cfg.AI_PRICE_ADJUSTMENT_MEDIUM = 0.10
    mock_cfg.AI_PRICE_ADJUSTMENT_LARGE = 0.15
    mock_cfg.PROFIT_HISTORY_TICKS = 10

    # Hiring Params
    mock_cfg.LABOR_ALPHA = 0.7
    mock_cfg.AUTOMATION_LABOR_REDUCTION = 0.5
    mock_cfg.LABOR_MARKET_MIN_WAGE = 8.0

    # Automation
    mock_cfg.AUTOMATION_COST_PER_PCT = 1000.0
    mock_cfg.FIRM_SAFETY_MARGIN = 2000.0
    mock_cfg.AUTOMATION_TAX_RATE = 0.05
    mock_cfg.CAPITAL_TO_OUTPUT_RATIO = 2.0
    mock_cfg.ALTMAN_Z_SCORE_THRESHOLD = 1.81
    mock_cfg.DIVIDEND_SUSPENSION_LOSS_TICKS = 3
    mock_cfg.DIVIDEND_RATE_MIN = 0.1
    mock_cfg.DIVIDEND_RATE_MAX = 0.5
    mock_cfg.SEVERANCE_PAY_WEEKS = 4

    # SEO
    mock_cfg.STARTUP_COST = 30000.0
    mock_cfg.SEO_TRIGGER_RATIO = 0.5
    mock_cfg.SEO_MAX_SELL_RATIO = 0.1

    return mock_cfg


@pytest.fixture
def mock_firm(mock_config):
    firm = Mock(spec=Firm)
    firm.id = 1
    firm.assets = 1000.0
    firm.employees = []
    firm.production_target = 100.0
    firm.inventory = {"food": 100.0}
    firm.productivity_factor = 1.0
    firm.last_prices = {"food": mock_config.GOODS_MARKET_SELL_PRICE}
    firm.revenue_this_turn = 0.0
    firm.cost_this_turn = 0.0
    firm.profit_history = deque(maxlen=mock_config.PROFIT_HISTORY_TICKS)
    firm.specialization = "food"
    firm.logger = MagicMock()
    firm.age = 25
    firm.finance = Mock()
    firm.finance.revenue_this_turn = 0.0
    firm.finance.last_revenue = 0.0
    firm.finance.calculate_altman_z_score.return_value = 3.0
    firm.finance.consecutive_loss_turns = 0
    firm.finance.last_sales_volume = 100.0
    firm.hr = Mock()
    firm.hr.employees = []
    firm.hr.employee_wages = {}
    firm.treasury_shares = 1000.0
    firm.research_history = {"total_spent": 0.0, "success_count": 0, "last_success_tick": 0}
    firm.base_quality = 1.0
    firm.sales = Mock()
    firm.production = Mock() # Add production mock
    firm.production.set_automation_level = Mock()
    firm.production.add_capital = Mock()
    firm.automation_level = 0.0
    firm.capital_stock = 100.0
    firm.system2_planner = Mock()
    firm.system2_planner.project_future.return_value = {} # Default guidance

    # Mock get_agent_data for AI
    firm.get_agent_data.return_value = {}

    return firm


@pytest.fixture
def mock_ai_engine():
    ai = Mock()
    # Default behavior: Neutral vector
    ai.decide_action_vector.return_value = FirmActionVector(
        sales_aggressiveness=0.5,
        hiring_aggressiveness=0.5,
        rd_aggressiveness=0.5,
        capital_aggressiveness=0.5,
        dividend_aggressiveness=0.5,
        debt_aggressiveness=0.5
    )
    return ai


@pytest.fixture
def firm_decision_engine_instance(mock_config, mock_ai_engine):
    engine = AIDrivenFirmDecisionEngine(
        ai_engine=mock_ai_engine, config_module=mock_config
    )
    # Remove old rule_based_engine mock injection
    return engine


class TestFirmDecisionEngine:
    def test_initialization(
        self, firm_decision_engine_instance, mock_ai_engine, mock_config
    ):
        assert firm_decision_engine_instance.corporate_manager is not None
        assert firm_decision_engine_instance.ai_engine == mock_ai_engine
        assert firm_decision_engine_instance.config_module == mock_config

    def test_make_decisions_overstock_reduces_target(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        mock_firm.inventory["food"] = 150.0 # Force overstock (150 > 100 * 1.2)
        initial_target = mock_firm.production_target

        context = DecisionContext(
            firm=mock_firm,
            markets={"food": Mock()},
            goods_data=[],
            market_data={},
            current_time=1,
            government=None,
        )
        firm_decision_engine_instance.make_decisions(context)

        expected_target = max(
            mock_config.FIRM_MIN_PRODUCTION_TARGET,
            initial_target * (1 - mock_config.PRODUCTION_ADJUSTMENT_FACTOR),
        )
        assert mock_firm.production_target == expected_target

    def test_make_decisions_understock_increases_target(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        mock_firm.inventory["food"] = 50.0
        initial_target = mock_firm.production_target

        context = DecisionContext(
            firm=mock_firm,
            markets={"food": Mock()},
            goods_data=[],
            market_data={},
            current_time=1,
            government=None,
        )
        firm_decision_engine_instance.make_decisions(context)

        expected_target = min(
            mock_config.FIRM_MAX_PRODUCTION_TARGET,
            initial_target * (1 + mock_config.PRODUCTION_ADJUSTMENT_FACTOR),
        )
        assert mock_firm.production_target == expected_target

    def test_make_decisions_target_within_bounds_no_change(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        mock_firm.inventory["food"] = 100.0
        initial_target = mock_firm.production_target

        context = DecisionContext(
            firm=mock_firm,
            markets={"food": Mock()},
            goods_data=[],
            market_data={},
            current_time=1,
            government=None,
        )
        firm_decision_engine_instance.make_decisions(context)

        assert mock_firm.production_target == initial_target

    def test_make_decisions_target_min_max_bounds(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        # Test min bound
        mock_firm.inventory["food"] = 1000.0
        mock_firm.production_target = mock_config.FIRM_MIN_PRODUCTION_TARGET * 0.5
        context = DecisionContext(
            firm=mock_firm,
            markets={"food": Mock()},
            goods_data=[],
            market_data={},
            current_time=1,
            government=None,
        )
        firm_decision_engine_instance.make_decisions(context)
        # Should increase to MIN (or at least move towards it? No, logic is reduce if overstock)
        # Wait, if overstock, we reduce target.
        # If target < MIN, max(MIN, new_target) -> MIN.
        assert mock_firm.production_target == mock_config.FIRM_MIN_PRODUCTION_TARGET

        # Test max bound
        mock_firm.inventory["food"] = 0.0
        mock_firm.production_target = mock_config.FIRM_MAX_PRODUCTION_TARGET * 1.5
        firm_decision_engine_instance.make_decisions(context)
        # If understock, increase target.
        # If target > MAX, min(MAX, new_target) -> MAX.
        assert mock_firm.production_target == mock_config.FIRM_MAX_PRODUCTION_TARGET

    def test_make_decisions_price_adjusts_overstock(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        mock_firm.inventory["food"] = 150.0
        mock_firm.last_prices["food"] = 10.0
        # Aggressiveness 0.5 (Neutral)

        context = DecisionContext(
            firm=mock_firm,
            markets={"food": Mock()},
            goods_data=[],
            market_data={},
            current_time=1,
            government=None,
        )
        firm_decision_engine_instance.make_decisions(context)

        # Check that post_ask was called with lower price
        # Price logic: target = market_price (10) * (1 + 0) * decay
        # decay < 1.0 due to overstock
        mock_firm.sales.post_ask.assert_called()
        args, _ = mock_firm.sales.post_ask.call_args
        price = args[1]
        assert price < 10.0

    def test_make_decisions_price_adjusts_understock(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        mock_firm.inventory["food"] = 90.0
        mock_firm.last_prices["food"] = 10.0
        # If inventory is low, decay is closer to 1.0 or 1.0.
        # But if aggressiveness is low (0.0 -> High Margin), price goes UP.
        # Let's set aggressiveness to 0.0 (High Margin Strategy)
        firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(
            sales_aggressiveness=0.0, # High Margin -> High Price
            hiring_aggressiveness=0.5,rd_aggressiveness=0.5,capital_aggressiveness=0.5,dividend_aggressiveness=0.5,debt_aggressiveness=0.5
        )

        context = DecisionContext(
            firm=mock_firm,
            markets={"food": Mock()},
            goods_data=[],
            market_data={"food": {"avg_price": 10.0}},
            current_time=1,
            government=None,
        )
        firm_decision_engine_instance.make_decisions(context)

        mock_firm.sales.post_ask.assert_called()
        args, _ = mock_firm.sales.post_ask.call_args
        price = args[1]
        assert price > 10.0

    def test_make_decisions_sell_order_details(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        mock_firm.inventory["food"] = 90.0
        mock_config.MAX_SELL_QUANTITY = 100.0

        context = DecisionContext(
            firm=mock_firm,
            markets={"food": Mock()}, # Market must exist
            goods_data=[],
            market_data={},
            current_time=1,
            government=None,
        )
        orders, _ = firm_decision_engine_instance.make_decisions(context)

        mock_firm.sales.post_ask.assert_called()
        args, _ = mock_firm.sales.post_ask.call_args
        item_id, price, qty, market, tick = args
        assert item_id == "food"
        assert qty == 90.0
        assert market is not None

    def test_make_decisions_hires_labor(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        """Verify BUY orders for labor when understaffed."""
        # 1. Setup Understaffed Firm
        # Target = 100. Gap = 100.
        # Production Fxn: L^alpha * K^beta.
        # Assume high gap to force hiring.
        mock_firm.production_target = 100.0
        mock_firm.inventory["food"] = 0.0
        mock_firm.hr.employees = [] # 0 Employees

        # 2. Aggressiveness for Hiring = 0.8 (High)
        firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(
            hiring_aggressiveness=0.8,
            sales_aggressiveness=0.5, rd_aggressiveness=0.5, capital_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5
        )

        context = DecisionContext(
            firm=mock_firm,
            markets={},
            goods_data=[],
            market_data={"labor": {"avg_wage": 10.0}},
            current_time=1,
            government=None,
        )

        # 3. Execution
        orders, _ = firm_decision_engine_instance.make_decisions(context)

        # 4. Verification
        labor_orders = [o for o in orders if o.item_id == "labor" and o.order_type == "BUY"]
        assert len(labor_orders) > 0
        assert labor_orders[0].price > 10.0 # High aggressiveness bids up wage
        assert labor_orders[0].quantity > 0

    def test_make_decisions_does_not_hire_when_full(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        """Verify no labor orders when employees >= needed."""
        # 1. Setup Full Firm
        mock_firm.production_target = 10.0
        mock_firm.inventory["food"] = 0.0
        # Assume 10 employees is enough for target 10
        mock_firm.hr.employees = [Mock(id=i, labor_skill=1.0) for i in range(100)]

        firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(
            hiring_aggressiveness=0.5,
            sales_aggressiveness=0.5, rd_aggressiveness=0.5, capital_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5
        )

        context = DecisionContext(
            firm=mock_firm,
            markets={},
            goods_data=[],
            market_data={"labor": {"avg_wage": 10.0}},
            current_time=1,
            government=None,
        )

        orders, _ = firm_decision_engine_instance.make_decisions(context)

        labor_orders = [o for o in orders if o.item_id == "labor" and o.order_type == "BUY"]
        assert len(labor_orders) == 0

    def test_make_decisions_fires_excess_labor(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        """Verify emp.quit() is called via finance.pay_severance when overstaffed."""
        # 1. Setup Overstaffed Firm
        mock_firm.production_target = 0.0 # No production needed
        mock_firm.inventory["food"] = 100.0 # Full inventory
        # 2 Employees, 1 Needed (Skeleton Crew)
        employee1 = Mock(id=1, labor_skill=1.0)
        employee1.quit = Mock()
        employee2 = Mock(id=2, labor_skill=1.0)
        employee2.quit = Mock()

        mock_firm.hr.employees = [employee1, employee2]
        mock_firm.hr.employee_wages = {1: 10.0, 2: 10.0}

        # Mock Finance to allow severance
        mock_firm.finance.pay_severance.return_value = True

        firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(
            hiring_aggressiveness=0.5,
            sales_aggressiveness=0.5, rd_aggressiveness=0.5, capital_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5
        )

        context = DecisionContext(
            firm=mock_firm,
            markets={},
            goods_data=[],
            market_data={"labor": {"avg_wage": 10.0}},
            current_time=1,
            government=None,
        )

        firm_decision_engine_instance.make_decisions(context)

        # 2. Verify Firing
        # FIFO firing: employee1 should be fired
        employee1.quit.assert_called_once()
        mock_firm.finance.pay_severance.assert_called_once()

    def test_sales_aggressiveness_impact_on_price(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        """Verify that sales aggressiveness inversely affects price."""
        mock_firm.inventory["food"] = 100.0
        mock_firm.last_prices["food"] = 10.0
        # No decay (100 vs 100) if target matched.
        # But we need markets.
        context = DecisionContext(
            firm=mock_firm,
            markets={"food": Mock()},
            goods_data=[],
            market_data={},
            current_time=1,
            government=None,
        )

        # 1. Low Aggressiveness (0.1) -> High Margin -> Higher Price
        firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(sales_aggressiveness=0.1, hiring_aggressiveness=0.5, rd_aggressiveness=0.5, capital_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5)
        firm_decision_engine_instance.make_decisions(context)
        args_low_agg, _ = mock_firm.sales.post_ask.call_args
        price_low_agg = args_low_agg[1]

        # 2. High Aggressiveness (0.9) -> High Volume -> Lower Price
        firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(sales_aggressiveness=0.9, hiring_aggressiveness=0.5, rd_aggressiveness=0.5, capital_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5)
        firm_decision_engine_instance.make_decisions(context)
        args_high_agg, _ = mock_firm.sales.post_ask.call_args
        price_high_agg = args_high_agg[1]

        assert price_low_agg > price_high_agg

    def test_rd_investment(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        """Verify R&D investment when aggressiveness is high."""
        # Setup High Cash
        mock_firm.assets = 100000.0
        firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(
            rd_aggressiveness=0.9,
            sales_aggressiveness=0.5, hiring_aggressiveness=0.5, capital_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5
        )

        context = DecisionContext(
            firm=mock_firm,
            markets={},
            goods_data=[],
            market_data={},
            current_time=1,
            government=None,
        )

        firm_decision_engine_instance.make_decisions(context)

        mock_firm.finance.invest_in_rd.assert_called()

    def test_capex_investment(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        """Verify Capex investment when aggressiveness is high."""
        # Setup High Cash
        mock_firm.assets = 100000.0
        firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(
            capital_aggressiveness=0.9,
            sales_aggressiveness=0.5, hiring_aggressiveness=0.5, rd_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5
        )

        context = DecisionContext(
            firm=mock_firm,
            markets={},
            goods_data=[],
            market_data={},
            current_time=1,
            government=None,
            reflux_system=Mock() # Reflux system needed for capex
        )

        firm_decision_engine_instance.make_decisions(context)

        mock_firm.finance.invest_in_capex.assert_called()

    def test_dividend_setting(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        """Verify dividend rate setting based on aggressiveness."""
        # Setup Healthy Firm
        mock_firm.finance.calculate_altman_z_score.return_value = 5.0 # Healthy
        mock_firm.finance.consecutive_loss_turns = 0

        firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(
            dividend_aggressiveness=0.9, # High Payout
            sales_aggressiveness=0.5, hiring_aggressiveness=0.5, rd_aggressiveness=0.5, capital_aggressiveness=0.5, debt_aggressiveness=0.5
        )

        context = DecisionContext(
            firm=mock_firm,
            markets={},
            goods_data=[],
            market_data={},
            current_time=1,
            government=None,
        )

        firm_decision_engine_instance.make_decisions(context)

        mock_firm.finance.set_dividend_rate.assert_called()
        # Verify rate is high
        args, _ = mock_firm.finance.set_dividend_rate.call_args
        rate = args[0]
        assert rate > 0.1 # Should be significantly higher than min
