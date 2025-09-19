import pytest
from unittest.mock import Mock, MagicMock, patch

from simulation.decisions.household_decision_engine import HouseholdDecisionEngine
from simulation.core_agents import Household
from simulation.ai_model import AIDecisionEngine
import config

# Mock Logger to prevent actual file writes during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('simulation.decisions.household_decision_engine.logging.getLogger') as mock_get_logger:
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        yield mock_logger_instance

# Correctly patch config values for all tests in this module
@pytest.fixture(autouse=True)
def set_config_for_tests():
    original_values = {}
    test_values = {
        'HOUSEHOLD_RESERVATION_PRICE_BASE': 5.0,
        'HOUSEHOLD_NEED_PRICE_MULTIPLIER': 1.0,
        'HOUSEHOLD_ASSET_PRICE_MULTIPLIER': 0.1,
        'HOUSEHOLD_PRICE_ELASTICITY_FACTOR': 0.5,
        'HOUSEHOLD_STOCKPILING_BONUS_FACTOR': 0.2,
        'MIN_SELL_PRICE': 1.0,
        'GOODS_MARKET_SELL_PRICE': 10.0,
        'SURVIVAL_NEED_THRESHOLD': 20.0,
        'LIQUIDITY_RATIO_MAX': 0.8,
        'LIQUIDITY_RATIO_MIN': 0.1,
        'LIQUIDITY_RATIO_DIVISOR': 100.0
    }

    for key, value in test_values.items():
        if hasattr(config, key):
            original_values[key] = getattr(config, key)
        setattr(config, key, value)
    
    yield
    
    # Restore original config values
    for key, value in original_values.items():
        setattr(config, key, value)

@pytest.fixture
def mock_household():
    hh = Mock(spec=Household)
    hh.id = 1
    hh.assets = 100.0
    hh.needs = {
        "survival_need": 50.0,
        "recognition_need": 20.0,
        "growth_need": 10.0,
        "wealth_need": 30.0,
        "imitation_need": 10.0,
        "labor_need": 0.0,
        "liquidity_need": 40.0
    }
    hh.inventory = {"food": 5.0}
    hh.perceived_avg_prices = {"food": 10.0}
    hh.goods_info_map = {
        "food": {"id": "food", "utility_per_need": {"survival_need": 1.0}, "storability": 0.5},
        "luxury_food": {"id": "luxury_food", "utility_per_need": {"recognition_need": 0.5}, "storability": 0.1}
    }
    return hh

@pytest.fixture
def mock_ai_engine():
    ai_engine = Mock(spec=AIDecisionEngine)
    ai_engine.make_decisions.return_value = [] # Default return value
    return ai_engine

@pytest.fixture
def household_decision_engine_instance(mock_ai_engine):
    return HouseholdDecisionEngine(goods_market=Mock(), labor_market=Mock(), loan_market=Mock(), ai_engine=mock_ai_engine)

class TestHouseholdDecisionEngine:
    def test_initialization(self, household_decision_engine_instance, mock_ai_engine):
        assert isinstance(household_decision_engine_instance.loan_market, Mock)
        assert household_decision_engine_instance.ai_engine == mock_ai_engine

    def test_calculate_reservation_price_basic(self, household_decision_engine_instance):
        hh = Mock(spec=Household)
        hh.id = 1
        hh.assets = 0.0
        hh.needs = {"survival_need": 0.0, "recognition_need": 0.0, "growth_need": 0.0}
        hh.inventory = {}
        hh.perceived_avg_prices = {}
        goods_data = [{"id": "food", "utility_per_need": {}, "storability": 0.0}]

        price = household_decision_engine_instance._calculate_reservation_price(hh, "food", {"goods_data": goods_data}, 1)
        expected_price = config.HOUSEHOLD_RESERVATION_PRICE_BASE
        assert price == pytest.approx(expected_price, rel=1e-2)

    def test_calculate_reservation_price_utility_bonus(self, household_decision_engine_instance):
        hh = Mock(spec=Household)
        hh.id = 1
        hh.assets = 0.0
        hh.needs = {"survival_need": 0.0, "recognition_need": 0.0, "growth_need": 0.0}
        hh.inventory = {}
        hh.perceived_avg_prices = {"food": 20.0} # Isolate utility bonus
        goods_data = [{"id": "food", "utility_per_need": {"survival_need": 10.0, "growth_need": 5.0}, "storability": 0.0}]

        price = household_decision_engine_instance._calculate_reservation_price(hh, "food", {"goods_data": goods_data}, 1)
        expected_utility_bonus = (10.0 + 5.0) * config.HOUSEHOLD_NEED_PRICE_MULTIPLIER
        expected_price = config.HOUSEHOLD_RESERVATION_PRICE_BASE + expected_utility_bonus
        assert price == pytest.approx(expected_price, rel=1e-2)

    def test_calculate_reservation_price_needs_bonus(self, household_decision_engine_instance):
        hh = Mock(spec=Household)
        hh.id = 1
        hh.assets = 0.0
        hh.needs = {"survival_need": 80.0, "recognition_need": 0.0, "growth_need": 0.0}
        hh.inventory = {}
        hh.perceived_avg_prices = {}
        goods_data = [{"id": "food", "utility_per_need": {"survival_need": 1.0}, "storability": 0.0}]

        price = household_decision_engine_instance._calculate_reservation_price(hh, "food", {"goods_data": goods_data}, 1)
        assert price > config.HOUSEHOLD_RESERVATION_PRICE_BASE

    def test_calculate_reservation_price_asset_bonus(self, household_decision_engine_instance):
        hh = Mock(spec=Household)
        hh.id = 1
        hh.assets = 500.0
        hh.needs = {"survival_need": 0.0, "recognition_need": 0.0, "growth_need": 0.0}
        hh.inventory = {}
        hh.perceived_avg_prices = {}
        goods_data = [{"id": "food", "utility_per_need": {}, "storability": 0.0}]

        price = household_decision_engine_instance._calculate_reservation_price(hh, "food", {"goods_data": goods_data}, 1)
        assert price > config.HOUSEHOLD_RESERVATION_PRICE_BASE

    def test_calculate_reservation_price_price_advantage_bonus(self, household_decision_engine_instance):
        hh = Mock(spec=Household)
        hh.id = 1
        hh.assets = 100.0  # Set assets to make reservation_price > perceived_price
        hh.needs = {"survival_need": 0.0, "recognition_need": 0.0, "growth_need": 0.0}
        hh.inventory = {}
        hh.perceived_avg_prices = {"food": 5.0}
        goods_data = [{"id": "food", "utility_per_need": {}, "storability": 0.0}]

        price = household_decision_engine_instance._calculate_reservation_price(hh, "food", {"goods_data": goods_data}, 1)
        assert price > config.HOUSEHOLD_RESERVATION_PRICE_BASE

    def test_calculate_reservation_price_stockpiling_bonus(self, household_decision_engine_instance):
        hh = Mock(spec=Household)
        hh.id = 1
        hh.assets = 0.0
        hh.needs = {"survival_need": 0.0, "recognition_need": 0.0, "growth_need": 0.0}
        hh.inventory = {"food": 0.0}
        hh.perceived_avg_prices = {"food": 10.0}
        goods_data = [{"id": "food", "utility_per_need": {}, "storability": 1.0}]

        price = household_decision_engine_instance._calculate_reservation_price(hh, "food", {"goods_data": goods_data}, 1)
        assert price > config.HOUSEHOLD_RESERVATION_PRICE_BASE

    def test_calculate_reservation_price_min_sell_price_bound(self, household_decision_engine_instance):
        hh = Mock(spec=Household)
        hh.id = 1
        hh.assets = 0.0
        hh.needs = {"survival_need": 0.0, "recognition_need": 0.0, "growth_need": 0.0}
        hh.inventory = {}
        hh.perceived_avg_prices = {}
        goods_data = [{"id": "food", "utility_per_need": {}, "storability": 0.0}]

        setattr(config, 'MIN_SELL_PRICE', 50.0) # Set a high min sell price
        price = household_decision_engine_instance._calculate_reservation_price(hh, "food", {"goods_data": goods_data}, 1)
        assert price == config.MIN_SELL_PRICE