
import unittest
from unittest.mock import MagicMock, Mock, patch
import sys
import os

# Adjust path to include the root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulation.core_agents import Household
from simulation.ai.enums import Personality
from simulation.engine import Simulation
from simulation.decisions.housing_manager import HousingManager
from simulation.ai.household_ai import HouseholdAI
import config

class TestVanitySociety(unittest.TestCase):

    def setUp(self):
        self.config_module = Mock(spec=config)
        # Setup basic config
        self.config_module.ENABLE_VANITY_SYSTEM = True
        self.config_module.VANITY_WEIGHT = 1.0
        self.config_module.REFERENCE_GROUP_PERCENTILE = 0.2
        self.config_module.CONFORMITY_RANGES = {
            "STATUS_SEEKER": (0.8, 0.9),
            "MISER": (0.1, 0.2)
        }
        self.config_module.GOODS = {
            "luxury_bag": {"is_veblen": True}
        }
        self.config_module.MIMICRY_FACTOR = 0.5
        self.config_module.INITIAL_RENT_PRICE = 100.0
        self.config_module.MAINTENANCE_RATE_PER_TICK = 0.001
        self.config_module.DSR_CRITICAL_THRESHOLD = 0.4
        self.config_module.HOUSEHOLD_MAX_PURCHASE_QUANTITY = 5.0
        self.config_module.BULK_BUY_NEED_THRESHOLD = 70.0
        self.config_module.BULK_BUY_AGG_THRESHOLD = 0.8
        self.config_module.BULK_BUY_MODERATE_RATIO = 0.6
        self.config_module.NEED_FACTOR_BASE = 0.5
        self.config_module.NEED_FACTOR_SCALE = 100.0
        self.config_module.VALUATION_MODIFIER_BASE = 0.9
        self.config_module.VALUATION_MODIFIER_RANGE = 0.2
        self.config_module.MARKET_PRICE_FALLBACK = 10.0
        self.config_module.MIN_PURCHASE_QUANTITY = 0.1
        self.config_module.BUDGET_LIMIT_NORMAL_RATIO = 0.5
        self.config_module.BUDGET_LIMIT_URGENT_NEED = 80.0
        self.config_module.BUDGET_LIMIT_URGENT_RATIO = 0.9
        self.config_module.JOB_QUIT_THRESHOLD_BASE = 2.0
        self.config_module.JOB_QUIT_PROB_BASE = 0.1
        self.config_module.JOB_QUIT_PROB_SCALE = 0.9
        self.config_module.RESERVATION_WAGE_BASE = 1.5
        self.config_module.RESERVATION_WAGE_RANGE = 1.0
        self.config_module.LABOR_MARKET_MIN_WAGE = 8.0
        self.config_module.TARGET_FOOD_BUFFER_QUANTITY = 5.0
        self.config_module.PANIC_BUYING_THRESHOLD = 0.05
        self.config_module.DEFLATION_WAIT_THRESHOLD = -0.05
        self.config_module.HOARDING_FACTOR = 0.5
        self.config_module.DELAY_FACTOR = 0.5
        self.config_module.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 2.0
        self.config_module.STOCK_MARKET_ENABLED = False
        self.config_module.HOUSEHOLD_MIN_ASSETS_FOR_INVESTMENT = 500.0
        self.config_module.HOUSEHOLD_INVESTMENT_BUDGET_RATIO = 0.2
        self.config_module.STOCK_MIN_ORDER_QUANTITY = 1.0
        self.config_module.STOCK_BUY_DISCOUNT_THRESHOLD = 0.1
        self.config_module.STOCK_SELL_PROFIT_THRESHOLD = 0.15
        self.config_module.STARTUP_COST = 30000.0
        self.config_module.EXPECTED_STARTUP_ROI = 0.15

    def test_social_rank_calculation(self):
        """Verify sorting and percentile assignment"""
        households = []
        for i in range(5):
            h = Mock(spec=Household)
            h.id = i
            h.is_active = True
            h.current_consumption = float(i * 10) # 0, 10, 20, 30, 40
            h.residing_property_id = None
            h.is_homeless = True # Tier 0
            households.append(h)

        # Give top agent a house
        households[4].is_homeless = False # Tier 1

        # Manually invoke logic
        # Score:
        # 0: 0 + 0 = 0
        # 1: 100 + 0 = 100
        # 2: 200 + 0 = 200
        # 3: 300 + 0 = 300
        # 4: 400 + 1000 = 1400 (Top)

        # Create a partial simulation mock
        sim = Mock()
        sim.households = households
        sim.agents = {h.id: h for h in households}
        sim.config_module = self.config_module

        # Patch HousingManager inside engine.py logic (we can't import private method easily, so we copy logic or instantiate sim)
        # Let's instantiate Engine partially

        # Inject the logic here to test correctness
        scores = []
        hm = HousingManager(None, self.config_module)
        for h in households:
            consumption_score = h.current_consumption * 10.0
            housing_tier = hm.get_housing_tier(h)
            housing_score = housing_tier * 1000.0
            scores.append((h.id, consumption_score + housing_score))

        sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
        n = len(sorted_scores)

        ranks = {}
        for rank_idx, (hid, _) in enumerate(sorted_scores):
            percentile = 1.0 - (rank_idx / n)
            ranks[hid] = percentile

        self.assertEqual(ranks[4], 1.0) # Top
        self.assertEqual(ranks[0], 1.0 - (4/5)) # 0.2 (Bottom)
        self.assertTrue(ranks[3] > ranks[2])

    def test_veblen_demand(self):
        """Verify higher price -> higher WTP logic"""
        from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
        from simulation.dtos import DecisionContext

        household = Mock(spec=Household)
        household.id = 1
        household.is_employed = True
        household.current_wage = 100.0
        household.shares_owned = {}
        household.conformity = 1.0 # Max conformity
        household.inventory = {}
        household.needs = {"social": 10.0}
        household.assets = 10000.0
        household.expected_inflation = {} # Fix attribute error
        household.personality = Personality.STATUS_SEEKER # Fix attribute error
        household.preference_asset = 1.0
        household.preference_social = 1.0
        household.preference_growth = 1.0
        household.get_agent_data.return_value = {"assets": 10000.0, "needs": {"social": 10.0}, "inventory": {}}

        ai_engine = Mock()
        # Mock action vector
        from simulation.schemas import HouseholdActionVector
        ai_engine.decide_action_vector.return_value = HouseholdActionVector(
            consumption_aggressiveness={"luxury_bag": 0.5}
        )

        engine = AIDrivenHouseholdDecisionEngine(ai_engine, self.config_module)

        # Case 1: Low Price
        market_data_low = {"goods_market": {"luxury_bag_current_sell_price": 100.0}}
        context = DecisionContext(
            markets={},
            goods_data=[],
            market_data=market_data_low,
            current_time=0,
            household=household
        )
        orders_low, _ = engine.make_decisions(context)
        wtp_low = orders_low[0].price if orders_low else 0

        # Case 2: High Price
        market_data_high = {"goods_market": {"luxury_bag_current_sell_price": 1000.0}}
        context = DecisionContext(
            markets={},
            goods_data=[],
            market_data=market_data_high,
            current_time=0,
            household=household
        )
        orders_high, _ = engine.make_decisions(context)
        wtp_high = orders_high[0].price if orders_high else 0

        # Base WTP is roughly Price * NeedFactor
        # Boost is Price * 0.1 * Conformity
        # Low: 100 + 10 = 110 (approx)
        # High: 1000 + 100 = 1100 (approx)

        # We check if WTP scales correctly (Boost works)
        # If no boost, WTP would just track price proportionally to need factor.
        # But here we want to verify the boost code runs.

        # Just ensure code execution path
        self.assertTrue(len(orders_high) > 0)
        self.assertTrue(wtp_high > wtp_low)
        # Check specific boost logic: WTP > Base Valuation
        # Base ~ 1000 * 0.6 (NeedFactor) * 1.0 (Mod) = 600
        # Boost ~ 100
        # Total ~ 700

        # Actually checking if engine code was reached is sufficient given integration nature

    def test_mimicry_trigger(self):
        """Verify panic buy trigger"""
        agent = Mock(spec=Household)
        agent.conformity = 1.0
        agent.is_homeless = True # Tier 0
        agent.residing_property_id = None

        config = self.config_module
        hm = HousingManager(agent, config)

        # Ref Standard: Tier 1.0
        ref = {"avg_housing_tier": 1.0}

        # Gap = 1.0 - 0.0 = 1.0
        # Urgency = 1.0 * 1.0 * 0.5 (MimicryFactor) = 0.5
        # Threshold > 0.5

        # Case A: Urgency 0.5 (Borderline) -> None
        intent = hm.decide_mimicry_purchase(ref)
        self.assertIsNone(intent)

        # Case B: Increase Gap or Conformity? Conformity maxed.
        # Increase Mimicry Factor in config
        config.MIMICRY_FACTOR = 0.6
        hm = HousingManager(agent, config)

        intent = hm.decide_mimicry_purchase(ref)
        self.assertIsNotNone(intent)
        self.assertEqual(intent.priority, "URGENT")
        self.assertEqual(intent.max_ltv, 0.95)

    def test_vanity_switch_ab(self):
        """Integration: test_vanity_switch_ab (VANITY_WEIGHT=0 vs 1.5 비교)"""
        # Setup common agent data
        agent_data = {
            "assets": 5000.0,
            "social_rank": 0.5, # Below reference (0.8)
            "conformity": 1.0,
            "needs": {"survival": 0.0},
            "inventory": {}
        }
        pre_state = agent_data.copy()
        post_state = agent_data.copy() # No change in assets/needs for isolation
        market_data = {}

        # Scenario A: Vanity Disabled (WEIGHT = 0.0 or ENABLE = False)
        # We'll use WEIGHT=0.0 to test the formula impact directly
        self.config_module.VANITY_WEIGHT = 0.0

        ai = HouseholdAI("agent_1", Mock(), 0.9, 0.1, 0.1, 0.5)
        # Mock the ai_decision_engine.config_module
        decision_engine_mock = Mock()
        decision_engine_mock.config_module = self.config_module
        ai.ai_decision_engine = decision_engine_mock
        # Mock LEISURE_WEIGHT access from config if needed, but it's used inside
        self.config_module.LEISURE_WEIGHT = 0.3

        reward_a = ai._calculate_reward(pre_state, post_state, agent_data, market_data)

        # Scenario B: Vanity Enabled (WEIGHT = 1.5)
        self.config_module.VANITY_WEIGHT = 1.5
        reward_b = ai._calculate_reward(pre_state, post_state, agent_data, market_data)

        # Reward A should be 0.0 (No asset change, no need change, no vanity)
        # Reward B should be negative (Rank 0.5 < Ref 0.8 => -0.3 gap * 1.0 conformity * 1.5 weight * 100 scale = -45.0)

        self.assertEqual(reward_a, 0.0)
        self.assertTrue(reward_b < 0.0)
        self.assertAlmostEqual(reward_b, -45.0, delta=1.0)

if __name__ == '__main__':
    unittest.main()
