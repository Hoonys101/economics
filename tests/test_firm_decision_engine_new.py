import pytest
from unittest.mock import Mock, MagicMock, patch

from simulation.decisions.firm_decision_engine import FirmDecisionEngine
from simulation.firms import Firm

# Mock Logger to prevent actual file writes during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('simulation.decisions.firm_decision_engine.logging.getLogger') as mock_get_logger:
        mock_logger_instance = MagicMock()
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
    mock_cfg.LABOR_MARKET_OFFERED_WAGE = 10.0
    mock_cfg.GOODS_MARKET_SELL_PRICE = 5.0
    mock_cfg.MIN_SELL_PRICE = 1.0
    mock_cfg.MAX_SELL_PRICE = 100.0
    mock_cfg.MAX_SELL_QUANTITY = 50.0
    mock_cfg.PRICE_ADJUSTMENT_FACTOR = 0.05
    mock_cfg.PRICE_ADJUSTMENT_EXPONENT = 1.2
    return mock_cfg

@pytest.fixture
def mock_firm(mock_config):
    firm = Mock(spec=Firm)
    firm.id = 1
    firm.assets = 1000.0
    firm.employees = []
    firm.production_targets = {"food": 100.0}
    firm.inventory = {"food": 100.0}
    firm.productivity_factor = 1.0
    firm.last_prices = {"food": mock_config.GOODS_MARKET_SELL_PRICE}
    firm.revenue_this_turn = 0.0
    firm.cost_this_turn = 0.0
    return firm

@pytest.fixture
def firm_decision_engine_instance(mock_config):
    return FirmDecisionEngine(config_module=mock_config, goods_market=Mock(), labor_market=Mock(), loan_market=Mock())

class TestFirmDecisionEngine:
    def test_initialization(self, firm_decision_engine_instance, mock_config):
        assert firm_decision_engine_instance.config_module == mock_config
        assert isinstance(firm_decision_engine_instance.goods_market, Mock)
        assert isinstance(firm_decision_engine_instance.labor_market, Mock)
        assert isinstance(firm_decision_engine_instance.loan_market, Mock)

    def test_make_decisions_overstock_reduces_target(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.inventory["food"] = 150.0 # 100 * 1.2 = 120, so 150 is overstocked
        initial_target = mock_firm.production_targets["food"]
        
        firm_decision_engine_instance.make_decisions(mock_firm, 1, {})
        
        expected_target = max(mock_config.FIRM_MIN_PRODUCTION_TARGET, initial_target * (1 - mock_config.PRODUCTION_ADJUSTMENT_FACTOR))
        assert mock_firm.production_targets["food"] == expected_target

    def test_make_decisions_understock_increases_target(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.inventory["food"] = 50.0 # 100 * 0.8 = 80, so 50 is understocked
        initial_target = mock_firm.production_targets["food"]
        
        firm_decision_engine_instance.make_decisions(mock_firm, 1, {})
        
        expected_target = min(mock_config.FIRM_MAX_PRODUCTION_TARGET, initial_target * (1 + mock_config.PRODUCTION_ADJUSTMENT_FACTOR))
        assert mock_firm.production_targets["food"] == expected_target

    def test_make_decisions_target_within_bounds_no_change(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.inventory["food"] = 100.0 # Exactly at target, within 0.8-1.2 bounds
        initial_target = mock_firm.production_targets["food"]
        
        firm_decision_engine_instance.make_decisions(mock_firm, 1, {})
        
        assert mock_firm.production_targets["food"] == initial_target

    def test_make_decisions_target_min_max_bounds(self, firm_decision_engine_instance, mock_firm, mock_config):
        # Test min bound
        mock_firm.inventory["food"] = 1000.0 # Force overstock
        mock_firm.production_targets["food"] = mock_config.FIRM_MIN_PRODUCTION_TARGET * 0.5 # Set target below min
        firm_decision_engine_instance.make_decisions(mock_firm, 1, {})
        assert mock_firm.production_targets["food"] == mock_config.FIRM_MIN_PRODUCTION_TARGET

        # Test max bound
        mock_firm.inventory["food"] = 0.0 # Force understock
        mock_firm.production_targets["food"] = mock_config.FIRM_MAX_PRODUCTION_TARGET * 1.5 # Set target above max
        firm_decision_engine_instance.make_decisions(mock_firm, 1, {})
        assert mock_firm.production_targets["food"] == mock_config.FIRM_MAX_PRODUCTION_TARGET

    def test_make_decisions_hires_to_meet_min_employees(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.employees = [] # No employees
        mock_firm.production_targets = {"food": 100} # Needs production
        
        orders = firm_decision_engine_instance.make_decisions(mock_firm, 1, {})
        
        buy_labor_orders = [o for o in orders if o.order_type == 'BUY' and o.item_id == 'labor']
        assert len(buy_labor_orders) > 0
        assert buy_labor_orders[0].quantity == 1.0
        assert buy_labor_orders[0].price == mock_config.LABOR_MARKET_OFFERED_WAGE
        assert buy_labor_orders[0].market_id == 'labor_market'

    def test_make_decisions_hires_for_needed_labor(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.employees = [Mock()] # One employee
        mock_firm.production_targets = {"food": 500} # High production target, needs more labor
        
        orders = firm_decision_engine_instance.make_decisions(mock_firm, 1, {})
        
        buy_labor_orders = [o for o in orders if o.order_type == 'BUY' and o.item_id == 'labor']
        assert len(buy_labor_orders) > 0
        assert buy_labor_orders[0].quantity == 1.0

    def test_make_decisions_does_not_hire_if_max_employees_reached(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.employees = [Mock() for _ in range(mock_config.FIRM_MAX_EMPLOYEES)] # Max employees
        mock_firm.production_targets = {"food": 500} # Needs production
        
        orders = firm_decision_engine_instance.make_decisions(mock_firm, 1, {})
        
        buy_labor_orders = [o for o in orders if o.order_type == 'BUY' and o.item_id == 'labor']
        assert len(buy_labor_orders) == 0

    def test_make_decisions_does_not_hire_if_no_needed_labor(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.employees = [Mock() for _ in range(10)] # Enough employees
        mock_firm.production_targets = {"food": 0} # No production needed
        mock_firm.inventory = {"food": 1000} # Plenty of inventory
        
        orders = firm_decision_engine_instance.make_decisions(mock_firm, 1, {})
        
        buy_labor_orders = [o for o in orders if o.order_type == 'BUY' and o.item_id == 'labor']
        assert len(buy_labor_orders) == 0

    def test_make_decisions_labor_order_details(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.employees = [] # Force hiring
        mock_firm.production_targets = {"food": 100} # Needs production
        
        orders = firm_decision_engine_instance.make_decisions(mock_firm, 1, {})
        
        labor_order = next((o for o in orders if o.order_type == 'BUY' and o.item_id == 'labor'), None)
        assert labor_order is not None
        assert labor_order.agent_id == mock_firm.id
        assert labor_order.quantity == 1.0
        assert labor_order.price == mock_config.LABOR_MARKET_OFFERED_WAGE
        assert labor_order.market_id == 'labor_market'

    def test_make_decisions_sells_if_inventory_exists(self, firm_decision_engine_instance, mock_firm):
        mock_firm.inventory["food"] = 10.0 # Has inventory
        orders = firm_decision_engine_instance.make_decisions(mock_firm, 1, {})
        sell_orders = [o for o in orders if o.order_type == 'SELL' and o.item_id == 'food']
        assert len(sell_orders) > 0

    def test_make_decisions_does_not_sell_if_no_inventory(self, firm_decision_engine_instance, mock_firm):
        mock_firm.inventory["food"] = 0.0 # No inventory
        orders = firm_decision_engine_instance.make_decisions(mock_firm, 1, {})
        sell_orders = [o for o in orders if o.order_type == 'SELL' and o.item_id == 'food']
        assert len(sell_orders) == 0

    def test_make_decisions_price_adjusts_overstock(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.inventory["food"] = 150.0 # Overstocked
        mock_firm.last_prices["food"] = 10.0 # Base price
        orders = firm_decision_engine_instance.make_decisions(mock_firm, 1, {})
        sell_order = next((o for o in orders if o.order_type == 'SELL' and o.item_id == 'food'), None)
        assert sell_order.price < 10.0 # Price should be reduced

    def test_make_decisions_price_adjusts_understock(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.inventory["food"] = 50.0 # Understocked
        mock_firm.last_prices["food"] = 10.0 # Base price
        orders = firm_decision_engine_instance.make_decisions(mock_firm, 1, {})
        sell_order = next((o for o in orders if o.order_type == 'SELL' and o.item_id == 'food'), None)
        assert sell_order.price > 10.0 # Price should be increased

    def test_make_decisions_sell_price_min_max_bounds(self, firm_decision_engine_instance, mock_firm, mock_config):
        # Test min bound
        mock_firm.inventory["food"] = 150.0 # Overstocked
        mock_firm.last_prices["food"] = 1.0 # Base price, near min
        mock_config.MIN_SELL_PRICE = 5.0 # Set a higher min
        orders = firm_decision_engine_instance.make_decisions(mock_firm, 1, {})
        sell_order = next((o for o in orders if o.order_type == 'SELL' and o.item_id == 'food'), None)
        assert sell_order.price == mock_config.MIN_SELL_PRICE

        # Test max bound
        mock_firm.inventory["food"] = 50.0 # Understocked
        mock_firm.last_prices["food"] = 100.0 # Base price, near max
        mock_config.MAX_SELL_PRICE = 90.0 # Set a lower max
        orders = firm_decision_engine_instance.make_decisions(mock_firm, 1, {})
        sell_order = next((o for o in orders if o.order_type == 'SELL' and o.item_id == 'food'), None)
        assert sell_order.price == mock_config.MAX_SELL_PRICE

    def test_make_decisions_sell_quantity_max_bound(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.inventory["food"] = 100.0 # More than MAX_SELL_QUANTITY
        mock_config.MAX_SELL_QUANTITY = 20.0 # Set max sell quantity
        orders = firm_decision_engine_instance.make_decisions(mock_firm, 1, {})
        sell_order = next((o for o in orders if o.order_type == 'SELL' and o.item_id == 'food'), None)
        assert sell_order.quantity == mock_config.MAX_SELL_QUANTITY

    def test_make_decisions_sell_order_details(self, firm_decision_engine_instance, mock_firm, mock_config):
        mock_firm.inventory["food"] = 10.0
        orders = firm_decision_engine_instance.make_decisions(mock_firm, 1, {})
        sell_order = next((o for o in orders if o.order_type == 'SELL' and o.item_id == 'food'), None)
        assert sell_order is not None
        assert sell_order.agent_id == mock_firm.id
        assert sell_order.quantity == 10.0 # Should sell all if less than MAX_SELL_QUANTITY
        assert sell_order.market_id == 'goods_market'
