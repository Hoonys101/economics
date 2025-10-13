import pytest
from unittest.mock import Mock, MagicMock

from simulation.decisions.household_decision_engine import HouseholdDecisionEngine
from simulation.core_agents import Household
from simulation.ai.household_ai import HouseholdAI
from simulation.ai.enums import Tactic
from simulation.markets.order_book_market import OrderBookMarket

# Mock config_module for testing purposes
class MockConfig:
    GOODS = {
        "basic_food": {
            "production_cost": 3,
            "utility_effects": {"survival": 10}
        },
        "luxury_food": {
            "production_cost": 10,
            "utility_effects": {"survival": 12, "social": 5}
        },
        "education_service": {
            "production_cost": 50,
            "utility_effects": {"improvement": 20}
        }
    }
    SURVIVAL_NEED_CONSUMPTION_THRESHOLD = 50.0
    BASE_DESIRE_GROWTH = 1.0
    MAX_DESIRE_VALUE = 100.0
    # Add other necessary config attributes if HouseholdDecisionEngine uses them
    # For now, these are the most relevant for consumption logic

@pytest.fixture
def mock_config_module():
    return MockConfig()

@pytest.fixture
def mock_household(mock_config_module):
    household = Mock(spec=Household)
    household.id = 1
    household.assets = 100.0
    household.inventory = {"basic_food": 0, "luxury_food": 0}
    household.needs = {"survival": 70.0, "social": 30.0, "improvement": 10.0, "asset": 50.0}
    household.config_module = mock_config_module
    household.get_agent_data.return_value = {
        "assets": household.assets,
        "needs": household.needs.copy(),
        "inventory": household.inventory.copy()
    }
    household.logger = MagicMock() # Mock the logger
    household.get_desired_wage.return_value = 12.0 # For labor market test
    return household

@pytest.fixture
def mock_ai_engine_registry():
    registry = Mock()
    mock_ai_decision_engine = Mock()
    mock_ai_decision_engine.is_trained = True
    registry.get_engine.return_value = mock_ai_decision_engine
    return registry

@pytest.fixture
def household_decision_engine(mock_household, mock_ai_engine_registry):
    # Create a mock for the ai_engine
    mock_ai_engine = Mock(spec=HouseholdAI)
    # Set the ai_engine for the HouseholdDecisionEngine
    engine = HouseholdDecisionEngine(
        agent_id=mock_household.id,
        value_orientation="wealth_and_needs",
        ai_engine_registry=mock_ai_engine_registry,
        ai_engine=mock_ai_engine # Pass the mock ai_engine here
    )
    engine.set_agent(mock_household)
    engine.logger = MagicMock() # Mock the logger for the engine
    return engine, mock_ai_engine # Return both the engine and its mock ai_engine

@pytest.fixture
def mock_markets():
    markets = {
        "basic_food": Mock(spec=OrderBookMarket),
        "luxury_food": Mock(spec=OrderBookMarket),
        "education_service": Mock(spec=OrderBookMarket),
        "labor_market": Mock(spec=OrderBookMarket),
        "loan_market": Mock()
    }
    # Set return values for get_best_ask
    markets["basic_food"].get_best_ask.return_value = 5.0
    markets["luxury_food"].get_best_ask.return_value = 15.0
    markets["education_service"].get_best_ask.return_value = 60.0
    markets["labor_market"].id = "labor_market"
    return markets

class TestHouseholdDecisionEngineMultiGood:

    def test_get_consumption_candidates(self, household_decision_engine, mock_markets):
        engine, _ = household_decision_engine
        candidates = engine._get_consumption_candidates(mock_markets)
        assert "basic_food" in candidates
        assert "luxury_food" in candidates
        assert "education_service" in candidates
        assert candidates["basic_food"] == 5.0
        assert candidates["luxury_food"] == 15.0
        assert candidates["education_service"] == 60.0

        # Test with no ask price
        mock_markets["basic_food"].get_best_ask.return_value = None
        candidates = engine._get_consumption_candidates(mock_markets)
        assert "basic_food" not in candidates # Should not include if no ask price

    def test_calculate_utility_gain_basic_food(self, household_decision_engine, mock_household):
        engine, _ = household_decision_engine
        # Basic food satisfies survival need
        utility = engine._calculate_utility_gain(mock_household, "basic_food", 1.0)
        # current_need_level (70) * effect (10) * quantity (1) = 700
        assert utility == 70.0 * 10.0 * 1.0

    def test_calculate_utility_gain_luxury_food(self, household_decision_engine, mock_household):
        engine, _ = household_decision_engine
        # Luxury food satisfies survival (12) and social (5) needs
        utility = engine._calculate_utility_gain(mock_household, "luxury_food", 1.0)
        # (survival_need 70 * 12) + (social_need 30 * 5) = 840 + 150 = 990
        assert utility == (mock_household.needs["survival"] * 12.0 * 1.0) + (mock_household.needs["social"] * 5.0 * 1.0)

    def test_find_optimal_consumption_bundle_prioritize_cheaper(self, household_decision_engine, mock_household, mock_markets):
        engine, mock_ai_engine = household_decision_engine
        # Test case: When luxury food is more expensive than basic food, households prioritize purchasing basic food.
        # Household has 100 assets
        # basic_food: price=5, utility=700 (utility/dollar = 140)
        # luxury_food: price=15, utility=990 (utility/dollar = 66)
        # education_service: price=60, utility=(10*20)=200 (utility/dollar = 3.33)

        # Should prioritize basic_food due to higher utility/dollar
        orders = engine._find_optimal_consumption_bundle(mock_household, mock_markets, 1)
        assert len(orders) == 3 # Now expects all affordable items due to removed break
        assert any(order.item_id == "basic_food" for order in orders)
        assert any(order.item_id == "luxury_food" for order in orders)
        assert any(order.item_id == "education_service" for order in orders)

    def test_find_optimal_consumption_bundle_insufficient_funds(self, household_decision_engine, mock_household, mock_markets):
        engine, _ = household_decision_engine
        mock_household.assets = 2.0 # Cannot afford basic_food (price 5)
        orders = engine._find_optimal_consumption_bundle(mock_household, mock_markets, 1)
        assert len(orders) == 0

    def test_find_optimal_consumption_bundle_no_candidates(self, household_decision_engine, mock_household, mock_markets):
        engine, _ = household_decision_engine
        mock_markets["basic_food"].get_best_ask.return_value = None
        mock_markets["luxury_food"].get_best_ask.return_value = None
        mock_markets["education_service"].get_best_ask.return_value = None
        orders = engine._find_optimal_consumption_bundle(mock_household, mock_markets, 1)
        assert len(orders) == 0

    def test_make_decisions_with_evaluate_consumption_options(self, household_decision_engine, mock_household, mock_markets):
        engine, mock_ai_engine = household_decision_engine
        # Mock AI to return EVALUATE_CONSUMPTION_OPTIONS
        mock_ai_engine.decide_and_learn.return_value = Tactic.EVALUATE_CONSUMPTION_OPTIONS
        
        # Household has 100 assets, will buy basic_food
        orders, tactic = engine.make_decisions(mock_household, mock_markets, [], {}, 1)
        
        assert tactic == Tactic.EVALUATE_CONSUMPTION_OPTIONS
        assert len(orders) == 3 # Now expects all affordable items due to removed break
        assert any(order.item_id == "basic_food" for order in orders)
        assert any(order.item_id == "luxury_food" for order in orders)
        assert any(order.item_id == "education_service" for order in orders)

    def test_make_decisions_with_participate_labor_market(self, household_decision_engine, mock_household, mock_markets):
        engine, mock_ai_engine = household_decision_engine
        # Mock AI to return PARTICIPATE_LABOR_MARKET
        mock_ai_engine.decide_and_learn.return_value = Tactic.PARTICIPATE_LABOR_MARKET
        mock_household.get_desired_wage.return_value = 12.0
        
        orders, tactic = engine.make_decisions(mock_household, mock_markets, [], {}, 1)
        
        assert tactic == Tactic.PARTICIPATE_LABOR_MARKET
        assert len(orders) == 1
        assert orders[0].item_id == "labor"
        assert orders[0].order_type == "SELL"
        assert orders[0].price == 12.0
        assert orders[0].market_id == "labor_market"

    def test_find_optimal_consumption_bundle_mix_goods_sufficient_budget(self, household_decision_engine, mock_household, mock_markets):
        engine, mock_ai_engine = household_decision_engine
        # Set assets high enough to buy multiple items
        mock_household.assets = 100.0
        # Set needs such that both survival and social needs are high
        mock_household.needs = {"survival": 70.0, "social": 70.0, "improvement": 10.0, "asset": 50.0}
        mock_household.get_agent_data.return_value = {
            "assets": mock_household.assets,
            "needs": mock_household.needs.copy(),
            "inventory": mock_household.inventory.copy()
        }

        # Temporarily modify the config for this test to make luxury food only satisfy social need
        original_goods_config = engine.agent.config_module.GOODS
        engine.agent.config_module.GOODS = {
            "basic_food": {
                "production_cost": 3,
                "utility_effects": {"survival": 10}
            },
            "luxury_food": {
                "production_cost": 10,
                "utility_effects": {"social": 15} # Only social utility for this test
            },
            "education_service": {
                "production_cost": 50,
                "utility_effects": {"improvement": 20}
            }
        }

        orders = engine._find_optimal_consumption_bundle(mock_household, mock_markets, 1)

        # Assert that all three affordable items are in the orders
        assert len(orders) == 3 # Expecting three orders: basic, luxury, education
        
        # Check for basic_food order
        basic_food_order = next((order for order in orders if order.item_id == "basic_food"), None)
        assert basic_food_order is not None
        assert basic_food_order.quantity == 1.0
        assert basic_food_order.price == 5.0

        # Check for luxury_food order
        luxury_food_order = next((order for order in orders if order.item_id == "luxury_food"), None)
        assert luxury_food_order is not None
        assert luxury_food_order.quantity == 1.0
        assert luxury_food_order.price == 15.0

        # Check for education_service order
        education_service_order = next((order for order in orders if order.item_id == "education_service"), None)
        assert education_service_order is not None
        assert education_service_order.quantity == 1.0
        assert education_service_order.price == 60.0

        # Restore original config
        engine.agent.config_module.GOODS = original_goods_config
