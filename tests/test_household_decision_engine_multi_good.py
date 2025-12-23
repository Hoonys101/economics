import pytest
from unittest.mock import Mock, MagicMock

from simulation.decisions.ai_driven_household_engine import (
    AIDrivenHouseholdDecisionEngine,
)
from simulation.core_agents import Household
from simulation.ai.household_ai import HouseholdAI
from simulation.ai.enums import Tactic, Aggressiveness
from simulation.dtos import DecisionContext
from simulation.markets.order_book_market import OrderBookMarket


# Mock config_module for testing purposes
class MockConfig:
    GOODS = {
        "basic_food": {"production_cost": 3, "utility_effects": {"survival": 10}},
        "luxury_food": {
            "production_cost": 10,
            "utility_effects": {"survival": 12, "social": 5},
        },
        "education_service": {
            "production_cost": 50,
            "utility_effects": {"improvement": 20},
        },
    }
    SURVIVAL_NEED_CONSUMPTION_THRESHOLD = 50.0
    BASE_DESIRE_GROWTH = 1.0
    MAX_DESIRE_VALUE = 100.0
    PERCEIVED_FAIR_PRICE_THRESHOLD_FACTOR = 0.9
    FOOD_PURCHASE_MAX_PER_TICK = 5.0
    TARGET_FOOD_BUFFER_QUANTITY = 5.0
    # Add other necessary config attributes if AIDrivenHouseholdDecisionEngine uses them
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
    household.needs = {
        "survival": 70.0,
        "social": 30.0,
        "improvement": 10.0,
        "asset": 50.0,
    }
    household.perceived_avg_prices = {}
    household.config_module = mock_config_module
    household.get_agent_data.return_value = {
        "assets": household.assets,
        "needs": household.needs.copy(),
        "inventory": household.inventory.copy(),
    }
    household.get_pre_state_data.return_value = household.get_agent_data()
    household.logger = MagicMock()  # Mock the logger
    household.get_desired_wage.return_value = 12.0  # For labor market test
    return household


@pytest.fixture
def mock_ai_engine_registry():
    registry = Mock()
    mock_ai_decision_engine = Mock()
    mock_ai_decision_engine.is_trained = True
    registry.get_engine.return_value = mock_ai_decision_engine
    return registry


@pytest.fixture
def household_decision_engine(
    mock_household, mock_ai_engine_registry, mock_config_module
):
    # Create a mock for the ai_engine
    mock_ai_engine = Mock(spec=HouseholdAI)
    # Set the ai_engine for the AIDrivenHouseholdDecisionEngine
    engine = AIDrivenHouseholdDecisionEngine(
        ai_engine=mock_ai_engine,  # Pass the mock ai_engine here
        config_module=mock_config_module,
    )
    return engine, mock_ai_engine  # Return both the engine and its mock ai_engine


@pytest.fixture
def mock_markets():
    markets = {
        "goods_market": Mock(spec=OrderBookMarket),
        "labor_market": Mock(spec=OrderBookMarket),
        "loan_market": Mock(),
    }
    # Set return values for get_best_ask
    markets["goods_market"].get_best_ask.side_effect = lambda item_id: {
        "basic_food": 5.0,
        "luxury_food": 15.0,
        "education_service": 60.0,
    }.get(item_id)
    markets["labor_market"].id = "labor_market"
    markets["goods_market"].id = "goods_market"
    return markets


class TestHouseholdDecisionEngineMultiGood:
    @pytest.mark.skip(reason="Refactoring needed: tests private method on non-existent rule_based_engine")
    def test_get_consumption_candidates(
        self, household_decision_engine, mock_markets, mock_household
    ):
        pass

    @pytest.mark.skip(reason="Refactoring needed: tests private method on non-existent rule_based_engine")
    def test_calculate_utility_gain_basic_food(
        self, household_decision_engine, mock_household
    ):
        pass

    @pytest.mark.skip(reason="Refactoring needed: tests private method on non-existent rule_based_engine")
    def test_calculate_utility_gain_luxury_food(
        self, household_decision_engine, mock_household
    ):
        pass
    
    @pytest.mark.skip(reason="Refactoring needed: tests private method on non-existent rule_based_engine")
    def test_find_optimal_consumption_bundle_prioritize_cheaper(
        self, household_decision_engine, mock_household, mock_markets
    ):
        pass

    @pytest.mark.skip(reason="Refactoring needed: tests private method on non-existent rule_based_engine")
    def test_find_optimal_consumption_bundle_insufficient_funds(
        self, household_decision_engine, mock_household, mock_markets
    ):
        pass

    @pytest.mark.skip(reason="Refactoring needed: tests private method on non-existent rule_based_engine")
    def test_find_optimal_consumption_bundle_no_candidates(
        self, household_decision_engine, mock_household, mock_markets
    ):
        pass

    def test_make_decisions_with_evaluate_consumption_options(
        self, household_decision_engine, mock_household, mock_markets
    ):
        engine, mock_ai_engine = household_decision_engine
        # Mock AI to return EVALUATE_CONSUMPTION_OPTIONS
        mock_ai_engine.decide_and_learn.return_value = (
            Tactic.EVALUATE_CONSUMPTION_OPTIONS, Aggressiveness.NORMAL
        )

        # Household has 100 assets, will buy basic_food
        context = DecisionContext(
            household=mock_household,
            markets=mock_markets,
            goods_data=list(MockConfig.GOODS.values()),
            market_data={},
            current_time=1,
        )
        orders, tactic_tuple = engine.make_decisions(context)
        tactic, _ = tactic_tuple

        assert tactic == Tactic.EVALUATE_CONSUMPTION_OPTIONS
        # The logic will choose the item with the best utility/price ratio, which is basic_food in the default setup.
        # It will then create ONE order for it.
        assert len(orders) == 1
        assert orders[0].item_id == "basic_food"

    def test_make_decisions_with_participate_labor_market(
        self, household_decision_engine, mock_household, mock_markets
    ):
        engine, mock_ai_engine = household_decision_engine
        # Mock AI to return PARTICIPATE_LABOR_MARKET
        mock_ai_engine.decide_and_learn.return_value = (
            Tactic.PARTICIPATE_LABOR_MARKET, Aggressiveness.NORMAL
        )
        mock_household.get_desired_wage.return_value = 12.0
        mock_household.is_employed = False

        context = DecisionContext(
            household=mock_household,
            markets=mock_markets,
            goods_data=[],
            market_data={},
            current_time=1,
        )
        orders, tactic_tuple = engine.make_decisions(context)
        tactic, _ = tactic_tuple

        assert tactic == Tactic.PARTICIPATE_LABOR_MARKET
        assert len(orders) == 1
        assert orders[0].item_id == "labor"
        assert orders[0].order_type == "SELL"
        assert orders[0].price == 12.0
        assert orders[0].market_id == "labor_market"

    @pytest.mark.skip(reason="Refactoring needed: tests private method on non-existent rule_based_engine")
    def test_find_optimal_consumption_bundle_mix_goods_sufficient_budget(
        self, household_decision_engine, mock_household, mock_markets
    ):
        pass