import pytest
from unittest.mock import Mock, patch
import os
import sys

import config
from simulation.decisions.household_decision_engine import HouseholdDecisionEngine
from simulation.core_agents import Household

# 프로젝트 루트 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Patch the Logger class within the module where it's used
@pytest.fixture(autouse=True)
def mock_logger_patch():
    with patch('simulation.decisions.household_decision_engine.logging.getLogger') as mock_get_logger:
        mock_logger_instance = mock_get_logger.return_value
        mock_logger_instance.debug = Mock()
        mock_logger_instance.info = Mock()
        mock_logger_instance.warning = Mock()
        mock_logger_instance.error = Mock()
        yield mock_logger_instance

@pytest.fixture
def mock_ai_engine():
    mock_engine = Mock()
    mock_engine.make_decisions.return_value = [] # Default return value for make_decisions
    return mock_engine

@pytest.fixture
def sample_household():
    # Create a mock household with necessary attributes
    household = Mock(spec=Household)
    household.id = 1
    household.assets = 1000.0
    household.needs = {
        "survival_need": 50.0,
        "recognition_need": 20.0,
        "growth_need": 10.0,
        "wealth_need": 5.0,
        "imitation_need": 0.0,
        "child_rearing_need": 0.0,
        "labor_need": 0.0,
        "liquidity_need": 20.0 # Default liquidity need
    }
    household.inventory = {"food": 5.0}
    household.perceived_avg_prices = {"food": 10.0}
    household.goods_data = [
        {"id": "food", "utility_per_need": {"survival_need": 1.0}, "storability": 0.8},
        {"id": "luxury_good", "utility_per_need": {"recognition_need": 2.0}, "storability": 0.1, "is_luxury": True}
    ]
    household.is_employed = False
    household.skills = {}
    household.current_food_consumption = 0.0
    return household

@pytest.fixture
def sample_market_data():
    return {
        "time": 1,
        "goods_market": {
            "food_avg_traded_price": 12.0,
            "food_current_sell_price": 11.0,
            "food_best_ask": 11.0, # Add best_ask for rule-based logic
            "luxury_good_avg_traded_price": 100.0,
            "luxury_good_current_sell_price": 90.0
        },
        "labor_market": {"avg_wage": 15.0},
        "all_households": [], # Will be populated by test if needed
        "goods_data": [
            {"id": "food", "utility_per_need": {"survival_need": 1.0}, "storability": 0.8},
            {"id": "luxury_good", "utility_per_need": {"recognition_need": 2.0}, "storability": 0.1, "is_luxury": True}
        ]
    }

@pytest.fixture(autouse=True)
def set_config_for_tests():
    # Save original config values
    original_config = {}
    for attr in dir(config):
        if not attr.startswith('__') and not callable(getattr(config, attr)):
            original_config[attr] = getattr(config, attr)

    # Set test-specific config values
    config.HOUSEHOLD_RESERVATION_PRICE_BASE = 5.0
    config.HOUSEHOLD_NEED_PRICE_MULTIPLIER = 1.0
    config.HOUSEHOLD_ASSET_PRICE_MULTIPLIER = 0.1
    config.HOUSEHOLD_PRICE_ELASTICITY_FACTOR = 0.5
    config.HOUSEHOLD_STOCKPILING_BONUS_FACTOR = 0.2
    config.MIN_SELL_PRICE = 1.0
    config.GOODS_MARKET_SELL_PRICE = 10.0
    config.LABOR_NEED_THRESHOLD = 50.0
    config.HOUSEHOLD_MIN_WAGE_DEMAND = 10.0
    config.WAGE_DECAY_RATE = 0.9
    config.RND_WAGE_PREMIUM = 1.5
    config.GROWTH_NEED_THRESHOLD = 60.0
    config.IMITATION_NEED_THRESHOLD = 70.0
    config.IMITATION_ASSET_THRESHOLD = 500.0
    config.CHILD_REARING_NEED_THRESHOLD = 80.0
    config.CHILD_REARING_ASSET_THRESHOLD = 1000.0
    config.SURVIVAL_NEED_THRESHOLD = 30.0 # Set a clear threshold
    config.ASSETS_THRESHOLD_FOR_OTHER_ACTIONS = 200.0
    config.RECOGNITION_NEED_THRESHOLD = 40.0
    config.LIQUIDITY_RATIO_MAX = 0.8
    config.LIQUIDITY_RATIO_MIN = 0.1
    config.LIQUIDITY_RATIO_DIVISOR = 100.0

    yield

    # Restore original config values after test
    for attr, value in original_config.items():
        setattr(config, attr, value)


class TestHouseholdDecisionEngine:

    def test_calculate_reservation_price_basic(self, sample_household, sample_market_data, mock_logger_patch, mock_ai_engine):
        engine = HouseholdDecisionEngine(logger=mock_logger_patch, ai_engine=mock_ai_engine)
        # Test with food, basic calculation
        price = engine._calculate_reservation_price(sample_household, "food", sample_market_data, 1)
        assert price > config.MIN_SELL_PRICE
        assert isinstance(price, float)

    def test_calculate_reservation_price_with_high_need(self, sample_household, sample_market_data, mock_logger_patch, mock_ai_engine):
        engine = HouseholdDecisionEngine(logger=mock_logger_patch, ai_engine=mock_ai_engine)
        sample_household.needs["survival_need"] = 90.0 # High survival need
        price = engine._calculate_reservation_price(sample_household, "food", sample_market_data, 1)
        # Expect price to be higher due to high need
        assert price > config.HOUSEHOLD_RESERVATION_PRICE_BASE

    def test_make_decisions_buy_food_rule_based(self, sample_household, sample_market_data, mock_logger_patch, mock_ai_engine):
        engine = HouseholdDecisionEngine(logger=mock_logger_patch, ai_engine=mock_ai_engine)
        # Ensure household wants to buy food based on rules
        sample_household.needs["survival_need"] = 80.0 # High survival need, above threshold
        sample_household.inventory["food"] = 0.0 # No food in inventory
        
        orders = engine.make_decisions(sample_household, 1, sample_market_data)
        
        # Assert that a rule-based order was created
        assert len(orders) == 1
        buy_order = orders[0]
        assert buy_order.order_type == 'BUY'
        assert buy_order.item_id == 'food'
        assert buy_order.agent_id == sample_household.id
        assert buy_order.market_id == 'goods_market'
        assert buy_order.quantity > 0

        # Assert that the AI engine was NOT called
        mock_ai_engine.make_decisions.assert_not_called()

    def test_make_decisions_labor_supply_ai_based(self, sample_household, sample_market_data, mock_logger_patch, mock_ai_engine):
        engine = HouseholdDecisionEngine(logger=mock_logger_patch, ai_engine=mock_ai_engine)
        sample_household.is_employed = False
        sample_household.needs["survival_need"] = 10.0 # Low survival need to ensure AI is called
        sample_household.needs["labor_need"] = 40.0 # Below threshold to ensure AI is called
        
        # Mock AI engine to return a labor sell order
        mock_ai_engine.make_decisions.return_value = [Mock(order_type='SELL', item_id='labor', quantity=1.0, price=10.0, agent_id=sample_household.id, market_id='labor_market')]
        orders = engine.make_decisions(sample_household, 1, sample_market_data)
        
        # Assert AI was called and returned the mocked order
        mock_ai_engine.make_decisions.assert_called_once_with(sample_household, sample_market_data, 1)
        assert len(orders) == 1
        labor_order = orders[0]
        assert labor_order.order_type == 'SELL'
        assert labor_order.item_id == 'labor'

    def test_make_decisions_no_labor_supply_if_employed(self, sample_household, sample_market_data, mock_logger_patch, mock_ai_engine):
        engine = HouseholdDecisionEngine(logger=mock_logger_patch, ai_engine=mock_ai_engine)
        sample_household.is_employed = True
        sample_household.needs["survival_need"] = 10.0 # Low survival need
        sample_household.needs["labor_need"] = 60.0
        
        # Mock AI engine to return no orders
        mock_ai_engine.make_decisions.return_value = []
        orders = engine.make_decisions(sample_household, 1, sample_market_data)
        
        mock_ai_engine.make_decisions.assert_called_once_with(sample_household, sample_market_data, 1)
        assert len(orders) == 0

    def test_make_decisions_rnd_labor_supply_ai_based(self, sample_household, sample_market_data, mock_logger_patch, mock_ai_engine):
        engine = HouseholdDecisionEngine(logger=mock_logger_patch, ai_engine=mock_ai_engine)
        sample_household.is_employed = False
        sample_household.needs["survival_need"] = 10.0 # Low survival need
        sample_household.needs["growth_need"] = 70.0 # High growth need
        
        # Mock AI engine to return a research labor sell order
        mock_ai_engine.make_decisions.return_value = [Mock(order_type='SELL', item_id='research_labor', quantity=1.0, price=15.0, agent_id=sample_household.id, market_id='labor_market')]
        orders = engine.make_decisions(sample_household, 1, sample_market_data)
        
        mock_ai_engine.make_decisions.assert_called_once_with(sample_household, sample_market_data, 1)
        assert len(orders) == 1
        rnd_labor_order = orders[0]
        assert rnd_labor_order.item_id == 'research_labor'

    def test_make_decisions_imitation_behavior_ai_based(self, sample_household, sample_market_data, mock_logger_patch, mock_ai_engine):
        engine = HouseholdDecisionEngine(logger=mock_logger_patch, ai_engine=mock_ai_engine)
        sample_household.needs["survival_need"] = 10.0 # Low survival need
        sample_household.needs["imitation_need"] = 80.0
        sample_household.assets = 600.0
        
        # Mock AI engine to return an imitation buy order
        mock_ai_engine.make_decisions.return_value = [Mock(order_type='BUY', item_id='luxury_good', quantity=1.0, price=100.0, agent_id=sample_household.id, market_id='goods_market')]
        engine.make_decisions(sample_household, 1, sample_market_data)
        
        mock_ai_engine.make_decisions.assert_called_once_with(sample_household, sample_market_data, 1)

    def test_make_decisions_child_rearing_behavior_ai_based(self, sample_household, sample_market_data, mock_logger_patch, mock_ai_engine):
        engine = HouseholdDecisionEngine(logger=mock_logger_patch, ai_engine=mock_ai_engine)
        sample_household.needs["survival_need"] = 10.0 # Low survival need
        sample_household.needs["child_rearing_need"] = 90.0
        sample_household.assets = 1200.0
        
        # Mock AI engine to return a child rearing action
        mock_ai_engine.make_decisions.return_value = [Mock(order_type='ACTION', item_id='child_rearing', quantity=1.0, price=100.0, agent_id=sample_household.id, market_id='household_action')]
        engine.make_decisions(sample_household, 1, sample_market_data)
        
        mock_ai_engine.make_decisions.assert_called_once_with(sample_household, sample_market_data, 1)

    def test_make_decisions_other_consumption_and_investment_ai_based(self, sample_household, sample_market_data, mock_logger_patch, mock_ai_engine):
        engine = HouseholdDecisionEngine(logger=mock_logger_patch, ai_engine=mock_ai_engine)
        sample_household.needs["survival_need"] = 10.0
        sample_household.assets = 300.0
        sample_household.needs["recognition_need"] = 50.0
        sample_household.needs["growth_need"] = 70.0
        sample_household.needs["wealth_need"] = 60.1

        # Mock AI engine to return various orders
        mock_ai_engine.make_decisions.return_value = [
            Mock(order_type='BUY', item_id='luxury_good', quantity=1.0, price=100.0, agent_id=sample_household.id, market_id='goods_market')
        ]
        orders = engine.make_decisions(sample_household, 1, sample_market_data)

        mock_ai_engine.make_decisions.assert_called_once_with(sample_household, sample_market_data, 1)
        assert len(orders) == 1
        luxury_good_buy_order = next((o for o in orders if o.order_type == 'BUY' and o.item_id == 'luxury_good'), None)
        assert luxury_good_buy_order is not None