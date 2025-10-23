import pytest
from unittest.mock import Mock, MagicMock, patch
from collections import deque

from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.firms import Firm
from simulation.ai.enums import Tactic

# Mock Logger to prevent actual file writes during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('simulation.decisions.ai_driven_firm_engine.logging.getLogger') as mock_get_logger:
        mock_logger_instance = MagicMock(name='firm_decision_engine_logger')
        # ... (rest of the mock setup)
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
    # Add a mock for the logger attribute
    firm.logger = MagicMock()
    return firm

@pytest.fixture
def mock_ai_engine():
    return Mock()

@pytest.fixture
def firm_decision_engine_instance(mock_config, mock_ai_engine):
    engine = AIDrivenFirmDecisionEngine(ai_engine=mock_ai_engine, config_module=mock_config)
    engine.rule_based_engine._calculate_dynamic_wage_offer = Mock(return_value=10.0)
    return engine

class TestFirmDecisionEngine:
    def test_initialization(self, firm_decision_engine_instance, mock_ai_engine, mock_config):
        # Check that the internal rule_based_engine was created and configured
        assert firm_decision_engine_instance.rule_based_engine is not None
        assert firm_decision_engine_instance.ai_engine == mock_ai_engine
        assert firm_decision_engine_instance.config_module == mock_config

    def test_make_decisions_overstock_reduces_target(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.inventory["food"] = 150.0
        initial_target = mock_firm.production_target
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.ADJUST_PRODUCTION
        
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)
        
        expected_target = max(mock_config.FIRM_MIN_PRODUCTION_TARGET, initial_target * (1 - mock_config.PRODUCTION_ADJUSTMENT_FACTOR))
        assert mock_firm.production_target == expected_target

    def test_make_decisions_understock_increases_target(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.inventory["food"] = 50.0
        initial_target = mock_firm.production_target
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.ADJUST_PRODUCTION
        
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)
        
        expected_target = min(mock_config.FIRM_MAX_PRODUCTION_TARGET, initial_target * (1 + mock_config.PRODUCTION_ADJUSTMENT_FACTOR))
        assert mock_firm.production_target == expected_target

    def test_make_decisions_target_within_bounds_no_change(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.inventory["food"] = 100.0
        initial_target = mock_firm.production_target
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.ADJUST_PRODUCTION
        
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)
        
        assert mock_firm.production_target == initial_target

    def test_make_decisions_target_min_max_bounds(self, firm_decision_engine_instance, mock_firm, mock_config):
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.ADJUST_PRODUCTION
        # Test min bound
        mock_firm.inventory["food"] = 1000.0
        mock_firm.production_target = mock_config.FIRM_MIN_PRODUCTION_TARGET * 0.5
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)
        assert mock_firm.production_target == mock_config.FIRM_MIN_PRODUCTION_TARGET

        # Test max bound
        mock_firm.inventory["food"] = 0.0
        mock_firm.production_target = mock_config.FIRM_MAX_PRODUCTION_TARGET * 1.5
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)
        assert mock_firm.production_target == mock_config.FIRM_MAX_PRODUCTION_TARGET

    def test_make_decisions_hires_to_meet_min_employees(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.employees = []
        mock_firm.inventory["food"] = 0 # Ensure production is needed
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.ADJUST_WAGES
        
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {'avg_wage': 10.0}, 1)
        
        buy_labor_orders = [o for o in orders if o.order_type == 'BUY' and o.item_id == 'labor']
        assert len(buy_labor_orders) > 0
        assert buy_labor_orders[0].quantity == 1.0
        assert buy_labor_orders[0].market_id == 'labor_market'

    def test_make_decisions_hires_for_needed_labor(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.employees = [Mock()]
        mock_firm.production_target = 500
        mock_firm.inventory["food"] = 0 # Ensure production is needed
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.ADJUST_WAGES
        
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {'avg_wage': 10.0}, 1)
        
        buy_labor_orders = [o for o in orders if o.order_type == 'BUY' and o.item_id == 'labor']
        assert len(buy_labor_orders) > 0
        assert buy_labor_orders[0].quantity == 1.0

    def test_make_decisions_does_not_hire_if_max_employees_reached(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.employees = [Mock() for _ in range(mock_config.FIRM_MAX_EMPLOYEES)]
        mock_firm.production_target = 500
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.ADJUST_WAGES
        
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)
        
        buy_labor_orders = [o for o in orders if o.order_type == 'BUY' and o.item_id == 'labor']
        assert len(buy_labor_orders) == 0

    def test_make_decisions_does_not_hire_if_no_needed_labor(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.employees = [Mock() for _ in range(10)]
        mock_firm.production_target = 0
        mock_firm.inventory = {"food": 1000}
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.ADJUST_WAGES
        
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)
        
        buy_labor_orders = [o for o in orders if o.order_type == 'BUY' and o.item_id == 'labor']
        assert len(buy_labor_orders) == 0

    def test_make_decisions_labor_order_details(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.employees = []
        mock_firm.inventory["food"] = 0 # Ensure production is needed
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.ADJUST_WAGES
        
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {'avg_wage': 10.0}, 1)
        
        labor_order = next((o for o in orders if o.order_type == 'BUY' and o.item_id == 'labor'), None)
        assert labor_order is not None
        assert labor_order.agent_id == mock_firm.id
        assert labor_order.quantity == 1.0
        assert labor_order.market_id == 'labor_market'

    def test_make_decisions_does_not_sell_if_understocked(self, firm_decision_engine_instance, mock_firm):
        mock_firm.inventory["food"] = 10.0 # Understocked
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.ADJUST_PRICE
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)
        sell_orders = [o for o in orders if o.order_type == 'SELL' and o.item_id == 'food']
        assert len(sell_orders) == 0

    def test_make_decisions_does_not_sell_if_no_inventory(self, firm_decision_engine_instance, mock_firm):
        mock_firm.inventory["food"] = 0.0
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.ADJUST_PRICE
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)
        sell_orders = [o for o in orders if o.order_type == 'SELL' and o.item_id == 'food']
        assert len(sell_orders) == 0

    def test_make_decisions_price_adjusts_overstock(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.inventory["food"] = 150.0
        mock_firm.last_prices["food"] = 10.0
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.ADJUST_PRICE
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)
        sell_order = next((o for o in orders if o.order_type == 'SELL' and o.item_id == 'food'), None)
        assert sell_order.price < 10.0

    def test_make_decisions_price_adjusts_understock(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.inventory["food"] = 90.0 # Not understocked, but below target
        mock_firm.last_prices["food"] = 10.0
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.ADJUST_PRICE
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)
        sell_order = next((o for o in orders if o.order_type == 'SELL' and o.item_id == 'food'), None)
        assert sell_order.price > 10.0

    def test_make_decisions_sell_price_min_max_bounds(self, firm_decision_engine_instance, mock_firm, mock_config):
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.ADJUST_PRICE
        # Test min bound
        mock_firm.inventory["food"] = 150.0
        mock_firm.last_prices["food"] = 1.0
        mock_config.MIN_SELL_PRICE = 5.0
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)
        sell_order = next((o for o in orders if o.order_type == 'SELL' and o.item_id == 'food'), None)
        assert sell_order.price == mock_config.MIN_SELL_PRICE

        # Test max bound (price would go below MIN_SELL_PRICE)
        mock_firm.inventory["food"] = 90.0 # Not understocked
        mock_firm.last_prices["food"] = 100.0
        mock_config.MAX_SELL_PRICE = 90.0
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)
        sell_order = next((o for o in orders if o.order_type == 'SELL' and o.item_id == 'food'), None)
        assert sell_order.price == mock_config.MAX_SELL_PRICE

    def test_make_decisions_sell_quantity_max_bound(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.inventory["food"] = 100.0
        mock_config.MAX_SELL_QUANTITY = 20.0
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.ADJUST_PRICE
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)
        sell_order = next((o for o in orders if o.order_type == 'SELL' and o.item_id == 'food'), None)
        assert sell_order.quantity == mock_config.MAX_SELL_QUANTITY

    def test_make_decisions_sell_order_details(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.inventory["food"] = 90.0 # Not understocked
        mock_config.MAX_SELL_QUANTITY = 100.0 # Ensure max quantity is not the limiting factor
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.ADJUST_PRICE
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)
        sell_order = next((o for o in orders if o.order_type == 'SELL' and o.item_id == 'food'), None)
        assert sell_order is not None
        assert sell_order.agent_id == mock_firm.id
        assert sell_order.quantity == 90.0
        assert sell_order.market_id == 'goods_market'

    def test_make_decisions_ai_price_increase_small(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.inventory["food"] = 100.0
        mock_firm.last_prices["food"] = 10.0
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.PRICE_INCREASE_SMALL
        
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)
        
        sell_order = next((o for o in orders if o.order_type == 'SELL' and o.item_id == 'food'), None)
        assert sell_order is not None
        expected_price = 10.0 * (1 + mock_config.AI_PRICE_ADJUSTMENT_SMALL)
        assert sell_order.price == pytest.approx(expected_price)

    def test_make_decisions_ai_price_decrease_medium(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.inventory["food"] = 100.0
        mock_firm.last_prices["food"] = 10.0
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.PRICE_DECREASE_MEDIUM
        
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)
        
        sell_order = next((o for o in orders if o.order_type == 'SELL' and o.item_id == 'food'), None)
        assert sell_order is not None
        expected_price = 10.0 * (1 - mock_config.AI_PRICE_ADJUSTMENT_MEDIUM)
        assert sell_order.price == pytest.approx(expected_price)

    def test_make_decisions_ai_price_hold(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.inventory["food"] = 100.0
        mock_firm.last_prices["food"] = 10.0
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.PRICE_HOLD
        
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)
        
        sell_order = next((o for o in orders if o.order_type == 'SELL' and o.item_id == 'food'), None)
        assert sell_order is not None
        expected_price = 10.0
        assert sell_order.price == pytest.approx(expected_price)

    def test_make_decisions_ai_price_min_max_bounds(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.inventory["food"] = 100.0
        mock_firm.last_prices["food"] = 1.0
        mock_config.MIN_SELL_PRICE = 5.0
        mock_config.MAX_SELL_PRICE = 90.0
        
        # Test min bound (price would go below MIN_SELL_PRICE)
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.PRICE_DECREASE_MEDIUM
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)
        sell_order = next((o for o in orders if o.order_type == 'SELL' and o.item_id == 'food'), None)
        assert sell_order.price == pytest.approx(mock_config.MIN_SELL_PRICE)

        # Test max bound (price would go above MAX_SELL_PRICE)
        mock_firm.last_prices["food"] = 95.0
        firm_decision_engine_instance.ai_engine.decide_and_learn.return_value = Tactic.PRICE_INCREASE_SMALL
        orders, _ = firm_decision_engine_instance.make_decisions(mock_firm, {}, [], {}, 1)
        sell_order = next((o for o in orders if o.order_type == 'SELL' and o.item_id == 'food'), None)
        assert sell_order.price == pytest.approx(mock_config.MAX_SELL_PRICE)