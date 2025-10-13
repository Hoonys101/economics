import pytest
from unittest.mock import Mock, MagicMock, patch

from simulation.decisions.household_decision_engine import HouseholdDecisionEngine
from simulation.core_agents import Household
from simulation.ai_model import AIDecisionEngine, AIEngineRegistry
from simulation.ai.enums import Tactic
from simulation.models import Order
import config

# Mock Logger to prevent actual file writes during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch('simulation.decisions.household_decision_engine.logging.getLogger') as mock_get_logger:
        mock_logger_instance = MagicMock(name='household_decision_engine_logger')
        mock_logger_instance.debug = MagicMock()
        mock_logger_instance.info = MagicMock()
        mock_logger_instance.warning = MagicMock()
        mock_logger_instance.error = MagicMock()
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
    hh.get_agent_data.return_value = {} # Mock the method
    hh.get_pre_state_data.return_value = {} # Mock the method
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
def mock_ai_engine_registry():
    registry = Mock(spec=AIEngineRegistry)
    # This is the mock for the HouseholdAI instance
    mock_ai_engine_instance = MagicMock() 
    mock_ai_engine_instance.decide_and_learn = Mock(return_value=Tactic.DO_NOTHING) # Default return
    
    # This is the mock for the AIDecisionEngine (the ML model wrapper)
    mock_ai_decision_engine_instance = Mock(spec=AIDecisionEngine)

    # When HouseholdDecisionEngine asks the registry for an engine, it gets the ML model wrapper
    registry.get_engine.return_value = mock_ai_decision_engine_instance
    
    # We also need to control what the HouseholdAI instance is. We'll patch its creation.
    with patch('simulation.decisions.household_decision_engine.HouseholdAI', return_value=mock_ai_engine_instance) as patched_ai:
        yield registry, mock_ai_engine_instance


@pytest.fixture
def household_decision_engine_instance(mock_ai_engine_registry):
    # mock_ai_engine_registry is now a tuple: (registry, mock_ai_engine_instance)
    registry, mock_ai_engine = mock_ai_engine_registry
    return HouseholdDecisionEngine(agent_id=1, value_orientation="test", ai_engine_registry=registry)

class TestHouseholdDecisionEngine:
    def test_initialization(self, household_decision_engine_instance, mock_ai_engine_registry):
        registry, _ = mock_ai_engine_registry
        assert household_decision_engine_instance.ai_engine_registry == registry

    def test_make_decisions_calls_ai_and_executes_tactic(self, household_decision_engine_instance, mock_household, mock_ai_engine_registry):
        _, mock_ai_engine = mock_ai_engine_registry
        
        # 1. Mock the AI's decision
        expected_tactic = Tactic.BUY_ESSENTIAL_GOODS
        mock_ai_engine.decide_and_learn.return_value = expected_tactic

        # 2. Mock the execution result
        expected_orders = [Mock(spec=Order)]
        with patch.object(household_decision_engine_instance, '_execute_tactic', return_value=expected_orders) as mock_execute:
            
            # 3. Call the method under test
            orders, tactic = household_decision_engine_instance.make_decisions(mock_household, {}, [], {}, 1)
            
            # 4. Assert AI was called correctly
            mock_ai_engine.decide_and_learn.assert_called_once()
            
            # 5. Assert the tactic was executed
            mock_execute.assert_called_once_with(expected_tactic, mock_household, {}, 1)
            
            # 6. Assert the final results are correct
            assert orders == expected_orders
            assert tactic == expected_tactic
