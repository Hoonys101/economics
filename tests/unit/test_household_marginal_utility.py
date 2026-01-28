
import unittest
from unittest.mock import MagicMock, patch
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.core_agents import Household, Talent
from simulation.ai.household_ai import HouseholdAI
from simulation.ai.enums import Tactic, Aggressiveness, Personality
from simulation.ai_model import AIDecisionEngine
from simulation.models import Order

class MockConfig:
    GOODS = {
        "food": {
            "id": "food",
            "utility_effects": {"survival": 10.0}, # Base Utility = 10
            "production_cost": 5.0
        }
    }
    TARGET_FOOD_BUFFER_QUANTITY = 10
    PERCEIVED_FAIR_PRICE_THRESHOLD_FACTOR = 1.2
    FOOD_PURCHASE_MAX_PER_TICK = 50
    SURVIVAL_NEED_CONSUMPTION_THRESHOLD = 50
    BASE_DESIRE_GROWTH = 1.0
    HOUSEHOLD_MAX_PURCHASE_QUANTITY = 5.0
    LABOR_MARKET_MIN_WAGE = 8.0
    # New config constants for refactored code
    MARKET_PRICE_FALLBACK = 10.0
    NEED_FACTOR_BASE = 0.5
    NEED_FACTOR_SCALE = 100.0
    VALUATION_MODIFIER_BASE = 0.9
    VALUATION_MODIFIER_RANGE = 0.2
    BULK_BUY_NEED_THRESHOLD = 70.0
    BULK_BUY_AGG_THRESHOLD = 0.8
    BULK_BUY_MODERATE_RATIO = 0.6
    BUDGET_LIMIT_NORMAL_RATIO = 0.5
    BUDGET_LIMIT_URGENT_NEED = 80.0
    BUDGET_LIMIT_URGENT_RATIO = 0.9
    MIN_PURCHASE_QUANTITY = 0.1
    JOB_QUIT_THRESHOLD_BASE = 2.0
    JOB_QUIT_PROB_BASE = 0.1
    JOB_QUIT_PROB_SCALE = 0.9
    RESERVATION_WAGE_BASE = 1.5
    RESERVATION_WAGE_RANGE = 1.0


class TestHouseholdMarginalUtility(unittest.TestCase):
    def setUp(self):
        self.config = MockConfig()
        
        # Mock AI components
        self.mock_ai_decision_engine = MagicMock(spec=AIDecisionEngine)
        self.ai_engine = HouseholdAI("agent_1", self.mock_ai_decision_engine)
        
        # Create Household
        talent = Talent(base_learning_rate=0.1, max_potential={})
        self.household = Household(
            id=1,
            talent=talent,
            goods_data=[self.config.GOODS["food"]],
            initial_assets=1000.0,
            initial_needs={"survival": 1.0},
            decision_engine=AIDrivenHouseholdDecisionEngine(self.ai_engine, self.config),
            value_orientation="N/A",
            personality=Personality.GROWTH_ORIENTED,
            config_module=self.config
        )
        # Give infinite money
        self.household._assets = 1_000_000_000
        self.household.inventory = {"food": 0}
        self.household.needs = {"survival": 1.0} # Needs > 0 to have utility

        self.engine = AIDrivenHouseholdDecisionEngine(self.ai_engine, self.config)

    def test_marginal_utility_stops_buying(self):
        """
        Test that purchasing stops when Marginal Utility < Price.
        Base Utility = 10 * 1 = 10.
        MU = 10 / (1 + Inventory)
        
        Scenario 1: Price = 2.0
        MU > 2.0 when Inventory < 4. (10/1=10, 10/2=5, 10/3=3.3, 10/4=2.5, 10/5=2.0)
        So it should buy exactly 4 or 5 units depending on <= or < logic.
        Code says: if marginal_utility > best_ask: buy.
        10/1 > 2 ? Yes (Buy 1st, Inv=0->1)
        10/2 > 2 ? Yes (Buy 2nd, Inv=1->2)
        10/3 > 2 ? Yes (Buy 3rd, Inv=2->3)
        10/4 > 2 ? Yes (Buy 4th, Inv=3->4)
        10/5 > 2 ? No (2 > 2 is False).
        So expected quantity = 4.
        """
        
        market_data = {
            "goods_market": MagicMock()
        }
        market_data["goods_market"].get_best_ask.return_value = 2.0 # Price = 2.0
        
        tactic = Tactic.BUY_BASIC_FOOD # Logic is shared in _handle_specific_purchase
        aggressiveness = Aggressiveness.NORMAL # Factor = 1.0

        # We need to call _handle_specific_purchase directly or simulate _execute_tactic
        # Let's call _handle_specific_purchase directly for unit testing logic
        
        orders = self.engine._handle_specific_purchase(
            self.household,
            "food",
            aggressiveness,
            current_tick=1,
            markets=market_data
        )
        
        self.assertTrue(len(orders) > 0)
        self.assertEqual(orders[0].quantity, 4)
        
    def test_high_price_prevents_buying(self):
        """
        Scenario 2: Price = 11.0
        Base Utility = 10.
        MU (first unit) = 10/1 = 10.
        10 > 11 ? No.
        Should buy 0 units.
        """
        market_data = {
            "goods_market": MagicMock()
        }
        market_data["goods_market"].get_best_ask.return_value = 11.0 # Price = 11.0
        
        orders = self.engine._handle_specific_purchase(
            self.household,
            "food",
            Aggressiveness.NORMAL,
            current_tick=1,
            markets=market_data
        )
        
        self.assertEqual(len(orders), 0)

if __name__ == "__main__":
    unittest.main()
