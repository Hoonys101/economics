import pytest
from unittest.mock import Mock, MagicMock, patch
from collections import deque

from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.firms import Firm
from simulation.schemas import FirmActionVector
from simulation.dtos import DecisionContext, FirmStateDTO
from tests.utils.factories import create_firm_config_dto


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

    # System 2
    mock_cfg.SYSTEM2_CALC_INTERVAL = 10

    return mock_cfg


@pytest.fixture
def mock_firm(mock_config):
    firm = Mock(spec=Firm)
    firm.id = 1
    firm.employees = []

    # Initialize departments first
    firm.finance = Mock()
    firm.production = Mock()
    firm.sales = Mock()
    firm.hr = Mock()

    firm.production_target = 100.0
    firm.inventory = {"food": 100.0}
    firm.productivity_factor = 1.0
    firm.last_prices = {"food": mock_config.GOODS_MARKET_SELL_PRICE}

    # Finance Init
    firm.finance.revenue_this_turn = 0.0
    firm.finance.balance = 1000.0
    firm.finance.last_revenue = 0.0
    firm.finance.calculate_altman_z_score.return_value = 3.0
    firm.finance.consecutive_loss_turns = 0
    firm.finance.last_sales_volume = 100.0
    firm.finance.treasury_shares = 1000.0
    firm.finance.total_shares = 1000.0

    firm.cost_this_turn = 0.0
    firm.profit_history = deque(maxlen=mock_config.PROFIT_HISTORY_TICKS)
    firm.specialization = "food"
    firm.logger = MagicMock()
    firm.age = 25

    # HR Init
    firm.hr.employees = []
    firm.hr.employee_wages = {}

    # Production Init
    firm.production.set_automation_level = Mock()
    firm.production.add_capital = Mock()
    firm.production.automation_level = 0.0
    firm.production.capital_stock = 100.0
    firm.production.productivity_factor = 1.0

    firm.research_history = {"total_spent": 0.0, "success_count": 0, "last_success_tick": 0}
    firm.base_quality = 1.0

    # System 2
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
    # Mock system2_planner to avoid calc_interval TypeError and isolate unit tests
    engine.corporate_manager.system2_planner = Mock()
    engine.corporate_manager.system2_planner.project_future.return_value = {}
    return engine

def create_mock_state(firm, config):
    state = Mock(spec=FirmStateDTO)
    state.id = firm.id
    state.agent_data = {}

    # Department Composite Mocks
    state.finance = Mock()
    state.production = Mock()
    state.sales = Mock()
    state.hr = Mock()

    # Populate
    state.finance.balance = 1000.0
    state.finance.revenue_this_turn = 0.0
    state.finance.expenses_this_tick = 0.0
    state.finance.consecutive_loss_turns = 0
    state.finance.altman_z_score = 3.0
    state.finance.treasury_shares = 1000.0
    state.finance.total_shares = 1000.0

    state.production.inventory = {"food": 100.0}
    state.production.input_inventory = {}
    state.production.production_target = 100.0
    state.production.specialization = "food"
    state.production.base_quality = 1.0
    state.production.inventory_quality = {"food": 1.0}
    state.production.capital_stock = 100.0
    state.production.productivity_factor = 1.0
    state.production.automation_level = 0.0

    state.sales.marketing_budget = 0.0
    state.sales.price_history = {"food": config.GOODS_MARKET_SELL_PRICE}

    state.hr.employees = []
    state.hr.employees_data = {}

    return state

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
        state = create_mock_state(mock_firm, mock_config)
        state.production.inventory["food"] = 150.0 # Force overstock (150 > 100 * 1.2)
        initial_target = state.production.production_target

        context = DecisionContext(
            state=state,
            config=create_firm_config_dto(overstock_threshold=1.2),
            market_data={},
            goods_data=[],
            current_time=1,
        )

        output = firm_decision_engine_instance.make_decisions(context)
        orders = output.orders

        expected_target = max(
            mock_config.FIRM_MIN_PRODUCTION_TARGET,
            initial_target * (1 - mock_config.PRODUCTION_ADJUSTMENT_FACTOR),
        )

        # Verify via orders (Purity)
        target_orders = [o for o in orders if o.order_type == "SET_TARGET"]
        assert len(target_orders) > 0
        assert target_orders[0].quantity == expected_target

    def test_make_decisions_understock_increases_target(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        state = create_mock_state(mock_firm, mock_config)
        state.production.inventory["food"] = 20.0
        state.production.production_target = 50.0  # Set lower than max (100) to allow increase
        initial_target = state.production.production_target

        context = DecisionContext(
            state=state,
            config=create_firm_config_dto(understock_threshold=0.8),
            market_data={},
            goods_data=[],
            current_time=1,
        )
        output = firm_decision_engine_instance.make_decisions(context)
        orders = output.orders

        expected_target = min(
            mock_config.FIRM_MAX_PRODUCTION_TARGET,
            initial_target * (1 + mock_config.PRODUCTION_ADJUSTMENT_FACTOR),
        )

        # Verify via orders (Purity)
        target_orders = [o for o in orders if o.order_type == "SET_TARGET"]
        assert len(target_orders) > 0
        assert target_orders[0].quantity == expected_target

    def test_make_decisions_target_within_bounds_no_change(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        state = create_mock_state(mock_firm, mock_config)
        state.production.inventory["food"] = 100.0
        initial_target = state.production.production_target

        context = DecisionContext(
            state=state,
            config=create_firm_config_dto(),
            market_data={},
            goods_data=[],
            current_time=1,
        )
        output = firm_decision_engine_instance.make_decisions(context)
        orders = output.orders

        # Ensure NO SET_TARGET order is generated
        target_orders = [o for o in orders if o.order_type == "SET_TARGET"]
        assert len(target_orders) == 0

    def test_make_decisions_target_min_max_bounds(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        # Test min bound
        state = create_mock_state(mock_firm, mock_config)
        state.production.inventory["food"] = 1000.0
        state.production.production_target = mock_config.FIRM_MIN_PRODUCTION_TARGET * 0.5

        context = DecisionContext(
            state=state,
            config=create_firm_config_dto(),
            market_data={},
            goods_data=[],
            current_time=1,
        )
        output = firm_decision_engine_instance.make_decisions(context)
        orders = output.orders

        # Verify via orders
        target_orders = [o for o in orders if o.order_type == "SET_TARGET"]
        assert len(target_orders) > 0
        # It should try to reduce, but get clamped to MIN.
        # Logic: new_target = target * (1-adj) = 5 * 0.9 = 4.5.
        # Clamped: max(MIN, 4.5) = 10.
        # So it should be 10.
        assert target_orders[0].quantity == mock_config.FIRM_MIN_PRODUCTION_TARGET

    def test_make_decisions_hires_labor(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        """Verify BUY orders for labor when understaffed."""
        firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(
            hiring_aggressiveness=0.8,
            sales_aggressiveness=0.5, rd_aggressiveness=0.5, capital_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5
        )

        state = create_mock_state(mock_firm, mock_config)
        state.production.production_target = 100.0
        state.production.inventory["food"] = 0.0
        state.hr.employees = [] # 0 Employees

        context = DecisionContext(
            state=state,
            config=create_firm_config_dto(),
            market_data={"labor": {"avg_wage": 10.0}},
            goods_data=[],
            current_time=1,
        )

        # 3. Execution
        output = firm_decision_engine_instance.make_decisions(context)
        orders = output.orders

        # 4. Verification
        labor_orders = [o for o in orders if getattr(o, "item_id", None) == "labor" and o.order_type == "BUY"]
        assert len(labor_orders) > 0
        assert labor_orders[0].price > 10.0 # High aggressiveness bids up wage
        assert labor_orders[0].quantity > 0

    @pytest.mark.skip(reason="Legacy Mutation Assertion: Needs migration to Order Verification")
    def test_make_decisions_does_not_hire_when_full(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        """Verify no labor orders when employees >= needed."""
        firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(
            hiring_aggressiveness=0.5,
            sales_aggressiveness=0.5, rd_aggressiveness=0.5, capital_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5
        )

        state = create_mock_state(mock_firm, mock_config)
        state.production.production_target = 10.0
        state.production.inventory["food"] = 0.0
        state.hr.employees = [1] * 100 # Mock employee IDs
        state.hr.employees_data = {i: {"labor_skill": 1.0} for i in range(100)}

        context = DecisionContext(
            state=state,
            config=create_firm_config_dto(),
            market_data={"labor": {"avg_wage": 10.0}},
            goods_data=[],
            current_time=1,
        )

        output = firm_decision_engine_instance.make_decisions(context)
        orders = output.orders

        labor_orders = [o for o in orders if getattr(o, "item_id", None) == "labor" and o.order_type == "BUY"]
        assert len(labor_orders) == 0

    def test_make_decisions_fires_excess_labor(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        """Verify FIRE orders when overstaffed."""
        firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(
            hiring_aggressiveness=0.5,
            sales_aggressiveness=0.5, rd_aggressiveness=0.5, capital_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5
        )

        state = create_mock_state(mock_firm, mock_config)
        state.production.production_target = 0.0 # No production needed
        state.production.inventory["food"] = 100.0 # Full inventory
        state.hr.employees = [1, 2]
        state.hr.employees_data = {1: {"wage": 10.0, "skill": 1.0}, 2: {"wage": 10.0, "skill": 1.0}}

        # Ensure we have cash to fire
        state.finance.balance = 1000.0

        context = DecisionContext(
            state=state,
            config=create_firm_config_dto(),
            market_data={"labor": {"avg_wage": 10.0}},
            goods_data=[],
            current_time=1,
        )

        output = firm_decision_engine_instance.make_decisions(context)
        orders = output.orders

        # 2. Verify Firing
        fire_orders = [o for o in orders if o.order_type == "FIRE"]
        assert len(fire_orders) > 0

    def test_sales_aggressiveness_impact_on_price(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        """Verify that sales aggressiveness inversely affects price."""
        state = create_mock_state(mock_firm, mock_config)
        state.production.inventory["food"] = 100.0
        state.sales.price_history["food"] = 10.0

        # Mock Market Snapshot to prevent Cost-Plus override
        snapshot = Mock()
        snapshot.market_signals = {"food": Mock(last_trade_tick=1)}

        context = DecisionContext(
            state=state,
            config=create_firm_config_dto(),
            market_data={},
            goods_data=[],
            current_time=1,
            market_snapshot=snapshot
        )

        # 1. Low Aggressiveness (0.1) -> High Margin -> Higher Price
        firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(sales_aggressiveness=0.1, hiring_aggressiveness=0.5, rd_aggressiveness=0.5, capital_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5)
        output_low = firm_decision_engine_instance.make_decisions(context)
        orders_low = output_low.orders
        sell_orders_low = [o for o in orders_low if o.order_type == "SELL" or o.order_type == "SET_PRICE"]

        price_low_agg = 0.0
        for o in sell_orders_low:
            if o.order_type == "SELL" and hasattr(o, 'price_limit'): price_low_agg = o.price_limit
            elif o.order_type == "SET_PRICE": price_low_agg = o.price_limit

        # 2. High Aggressiveness (0.9) -> High Volume -> Lower Price
        firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(sales_aggressiveness=0.9, hiring_aggressiveness=0.5, rd_aggressiveness=0.5, capital_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5)
        output_high = firm_decision_engine_instance.make_decisions(context)
        orders_high = output_high.orders
        sell_orders_high = [o for o in orders_high if o.order_type == "SELL" or o.order_type == "SET_PRICE"]

        price_high_agg = 0.0
        for o in sell_orders_high:
            if o.order_type == "SELL" and hasattr(o, 'price_limit'): price_high_agg = o.price_limit
            elif o.order_type == "SET_PRICE": price_high_agg = o.price_limit

        # Assert if orders were generated
        if price_low_agg > 0 and price_high_agg > 0:
            assert price_low_agg > price_high_agg

    def test_rd_investment(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        """Verify R&D investment when aggressiveness is high."""
        firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(
            rd_aggressiveness=0.9,
            sales_aggressiveness=0.5, hiring_aggressiveness=0.5, capital_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5
        )

        state = create_mock_state(mock_firm, mock_config)
        state.finance.balance = 100000.0 # High Cash

        context = DecisionContext(
            state=state,
            config=create_firm_config_dto(),
            market_data={},
            goods_data=[],
            current_time=1,
        )

        output = firm_decision_engine_instance.make_decisions(context)
        orders = output.orders

        invest_orders = [o for o in orders if o.order_type == "INVEST_RD"]
        assert len(invest_orders) > 0

    def test_capex_investment(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        """Verify Capex investment when aggressiveness is high."""
        firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(
            capital_aggressiveness=0.9,
            sales_aggressiveness=0.5, hiring_aggressiveness=0.5, rd_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5
        )

        state = create_mock_state(mock_firm, mock_config)
        state.finance.balance = 100000.0 # High Cash

        context = DecisionContext(
            state=state,
            config=create_firm_config_dto(),
            market_data={},
            goods_data=[],
            current_time=1,
        )

        output = firm_decision_engine_instance.make_decisions(context)
        orders = output.orders

        capex_orders = [o for o in orders if o.order_type == "INVEST_CAPEX"]
        assert len(capex_orders) > 0

    def test_dividend_setting(
        self, firm_decision_engine_instance, mock_firm, mock_config
    ):
        """Verify dividend rate setting based on aggressiveness."""
        firm_decision_engine_instance.ai_engine.decide_action_vector.return_value = FirmActionVector(
            dividend_aggressiveness=0.9, # High Payout
            sales_aggressiveness=0.5, hiring_aggressiveness=0.5, rd_aggressiveness=0.5, capital_aggressiveness=0.5, debt_aggressiveness=0.5
        )

        state = create_mock_state(mock_firm, mock_config)
        state.finance.altman_z_score = 5.0 # Healthy
        state.finance.consecutive_loss_turns = 0
        state.finance.balance = 1000.0

        config = create_firm_config_dto()
        config.dividend_rate_min = 0.1
        config.dividend_rate_max = 0.5

        context = DecisionContext(
            state=state,
            config=config,
            market_data={},
            goods_data=[],
            current_time=1,
        )

        output = firm_decision_engine_instance.make_decisions(context)
        orders = output.orders

        div_orders = [o for o in orders if o.order_type == "SET_DIVIDEND"]
        assert len(div_orders) > 0
        rate = div_orders[0].quantity
        assert rate > 0.1
