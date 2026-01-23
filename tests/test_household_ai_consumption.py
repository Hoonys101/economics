import pytest
from unittest.mock import MagicMock
from simulation.core_agents import Household
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.ai.household_ai import HouseholdAI
from simulation.ai.enums import Tactic, Aggressiveness
from simulation.dtos import DecisionContext
from simulation.models import Order
import config

class TestHouseholdAIConsumption:
    @pytest.fixture
    def setup_household(self):
        # Create mocks
        mock_config = MagicMock()
        mock_config.SURVIVAL_NEED_THRESHOLD = 20.0
        mock_config.SURVIVAL_NEED_CONSUMPTION_THRESHOLD = 50.0 # High threshold
        mock_config.HOUSEHOLD_MIN_FOOD_INVENTORY = 2.0
        mock_config.PERCEIVED_FAIR_PRICE_THRESHOLD_FACTOR = 0.9
        mock_config.FOOD_PURCHASE_MAX_PER_TICK = 5.0
        mock_config.GOODS = {"food": {"utility_effects": {"survival": 10}}}
        
        mock_logger = MagicMock()
        
        # Mock HouseholdAI
        mock_household_ai = MagicMock(spec=HouseholdAI)
        # Mock decide_and_learn to return the tuple directly
        # Using Aggressiveness.PASSIVE as a placeholder if NEUTRAL doesn't exist
        mock_household_ai.decide_and_learn.return_value = (Tactic.EVALUATE_CONSUMPTION_OPTIONS, Aggressiveness.PASSIVE)
        
        engine = AIDrivenHouseholdDecisionEngine(mock_household_ai, mock_config, mock_logger)
        
        household = MagicMock(spec=Household)
        household.id = 1
        household.needs = {"survival": 80.0} # High survival need
        household.inventory = {"food": 0.0}
        household._assets = 100.0
        household.get_agent_data.return_value = {}
        household.get_pre_state_data.return_value = {}
        household.perceived_avg_prices = {"food": 10.0}
        
        return engine, household, mock_household_ai

    def test_ai_chooses_consumption_tactic(self, setup_household):
        engine, household, mock_household_ai = setup_household
        
        markets = {"goods_market": MagicMock()}
        # Mock get_best_ask for food
        markets["goods_market"].get_best_ask.return_value = 10.0
        
        goods_data = [{"id": "food", "name": "Food"}]
        market_data = {}
        current_time = 1
        
        # Run make_decisions
        context = DecisionContext(
            household=household,
            markets=markets,
            goods_data=goods_data,
            market_data=market_data,
            current_time=current_time,
        )
        orders, (tactic, aggressiveness) = engine.make_decisions(context)
        
        # Verify Tactic
        assert tactic == Tactic.EVALUATE_CONSUMPTION_OPTIONS
        
        # Verify AI decide_and_learn was called
        mock_household_ai.decide_and_learn.assert_called()
        
        # Verify Order Generation (EVALUATE_CONSUMPTION_OPTIONS logic)
        # The logic iterates GOODS, so we need config.GOODS to be set (which we did in setup)
        # And it checks markets["goods_market"].get_best_ask(item_id)
        
        # Check if any order was created
        assert len(orders) > 0
        assert orders[0].order_type == "BUY"
        # The logic might buy based on utility. "food" has utility.
        assert orders[0].item_id == "food"
