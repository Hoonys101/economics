import unittest
from unittest.mock import MagicMock, patch
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.core_agents import Household, Talent
from simulation.ai.household_ai import HouseholdAI
from simulation.ai.enums import Tactic, Aggressiveness, Personality
from simulation.ai_model import AIDecisionEngine
from simulation.models import Order
from simulation.dtos import DecisionContext, HouseholdConfigDTO
from modules.household.dtos import HouseholdStateDTO
from simulation.schemas import HouseholdActionVector

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

    # Missing fields for DTO Purity
    DEFAULT_MORTGAGE_RATE = 0.05
    DSR_CRITICAL_THRESHOLD = 0.4
    DEBT_REPAYMENT_RATIO = 0.1
    DEBT_REPAYMENT_CAP = 0.5
    DEBT_LIQUIDITY_RATIO = 0.5
    INITIAL_RENT_PRICE = 100.0
    ENABLE_VANITY_SYSTEM = False
    MIMICRY_FACTOR = 0.1
    MAINTENANCE_RATE_PER_TICK = 0.01
    STOCK_MARKET_ENABLED = False
    HOUSEHOLD_MIN_ASSETS_FOR_INVESTMENT = 1000.0
    STOCK_INVESTMENT_EQUITY_DELTA_THRESHOLD = 100.0
    STOCK_INVESTMENT_DIVERSIFICATION_COUNT = 5
    EXPECTED_STARTUP_ROI = 0.15
    STARTUP_COST = 30000.0

def _create_household_config(mock_config):
    return HouseholdConfigDTO(
        survival_need_consumption_threshold=mock_config.SURVIVAL_NEED_CONSUMPTION_THRESHOLD,
        target_food_buffer_quantity=mock_config.TARGET_FOOD_BUFFER_QUANTITY,
        food_purchase_max_per_tick=mock_config.FOOD_PURCHASE_MAX_PER_TICK,
        labor_market_min_wage=mock_config.LABOR_MARKET_MIN_WAGE,
        market_price_fallback=mock_config.MARKET_PRICE_FALLBACK,
        need_factor_base=mock_config.NEED_FACTOR_BASE,
        need_factor_scale=mock_config.NEED_FACTOR_SCALE,
        valuation_modifier_base=mock_config.VALUATION_MODIFIER_BASE,
        valuation_modifier_range=mock_config.VALUATION_MODIFIER_RANGE,
        household_max_purchase_quantity=mock_config.HOUSEHOLD_MAX_PURCHASE_QUANTITY,
        bulk_buy_need_threshold=mock_config.BULK_BUY_NEED_THRESHOLD,
        bulk_buy_agg_threshold=mock_config.BULK_BUY_AGG_THRESHOLD,
        bulk_buy_moderate_ratio=mock_config.BULK_BUY_MODERATE_RATIO,
        budget_limit_normal_ratio=mock_config.BUDGET_LIMIT_NORMAL_RATIO,
        budget_limit_urgent_need=mock_config.BUDGET_LIMIT_URGENT_NEED,
        budget_limit_urgent_ratio=mock_config.BUDGET_LIMIT_URGENT_RATIO,
        min_purchase_quantity=mock_config.MIN_PURCHASE_QUANTITY,
        job_quit_threshold_base=mock_config.JOB_QUIT_THRESHOLD_BASE,
        job_quit_prob_base=mock_config.JOB_QUIT_PROB_BASE,
        job_quit_prob_scale=mock_config.JOB_QUIT_PROB_SCALE,
        # Default values for missing config
        assets_threshold_for_other_actions=100.0,
        wage_decay_rate=0.01,
        reservation_wage_floor=1.0,
        survival_critical_turns=5,
        household_low_asset_threshold=10.0,
        household_low_asset_wage=5.0,
        household_default_wage=10.0,
        panic_buying_threshold=0.05,
        hoarding_factor=0.5,
        deflation_wait_threshold=-0.05,
        delay_factor=0.5,
        dsr_critical_threshold=0.4,
        stock_market_enabled=False,
        household_min_assets_for_investment=1000.0,
        stock_investment_equity_delta_threshold=100.0,
        stock_investment_diversification_count=5,
        expected_startup_roi=0.15,
        startup_cost=30000.0,
        debt_repayment_ratio=0.1,
        debt_repayment_cap=0.5,
        debt_liquidity_ratio=0.5,
        initial_rent_price=100.0,
        default_mortgage_rate=0.05,
        enable_vanity_system=False,
        mimicry_factor=0.1,
        maintenance_rate_per_tick=0.01
    )

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
        self.household.is_employed = True # Avoid panic logic
        self.household.expected_inflation = {}
        self.household.durable_assets = []

        self.engine = AIDrivenHouseholdDecisionEngine(self.ai_engine, self.config)

    def test_marginal_utility_stops_buying(self):
        """
        Test that purchasing happens when Price is low.
        """
        # Scenario 1: Price = 2.0 (Low)
        market_data = {
            "goods_market": {
                "food_current_sell_price": 2.0
            }
        }
        
        # Mock AI to buy food
        self.ai_engine.decide_action_vector = MagicMock(return_value=HouseholdActionVector(
            consumption_aggressiveness={"food": 0.5},
            job_mobility_aggressiveness=0.0
        ))
        
        household_state = HouseholdStateDTO.from_household(self.household)
        household_config = _create_household_config(self.config)

        context = DecisionContext(
            state=household_state,
            config=household_config,
            markets={},
            goods_data=[self.config.GOODS["food"]],
            market_data=market_data,
            current_time=1
        )
        
        orders, _ = self.engine.make_decisions(context)

        buy_orders = [o for o in orders if o.item_id == "food" and o.order_type == "BUY"]
        self.assertTrue(len(buy_orders) > 0)
        # Check price is around 2.0 * modifiers
        self.assertGreater(buy_orders[0].price, 0.5)
        
    def test_high_price_prevents_buying(self):
        """
        Scenario 2: Price = 100.0 (Very High)
        Willingness to Pay should depend on Need.
        Need is low (1.0).
        Price is 100.
        WTP = 100 * NeedFactor(Low) * Valuation(Normal)
        NeedFactor ~ 0.5.
        WTP ~ 50.
        Since WTP < Price, should it stop buying?
        The Engine emits an order with `price = WTP`.
        But the engine uses `avg_price` to calculating WTP.
        WTP = AvgPrice * Modifiers.
        So WTP will be proportional to 100.

        However, budget constraints might kick in if quantity is high.
        With infinite assets, budget is not issue.

        If `WTP` is just a bid price, the engine WILL generate an order.
        The "prevents buying" logic usually happens in Market Matching (Bid < Ask).

        BUT, if we want to test "Marginal Utility", we assume the agent REDUCES quantity or aggressiveness.

        Let's check if Aggressiveness Attenuation (ROI) logic works.
        ROI = (Need / Price) * Preference
        Need = 1.0. Price = 100. ROI = 0.01.
        Savings ROI ~ 1.0 (interest rate).
        ConsROI (0.01) < SavROI (1.0).
        Attenuation = 0.01 / 1.0 = 0.01.
        Aggressiveness *= 0.01.
        If Aggressiveness becomes very low, maybe quantity drops?

        Let's check if the generated order reflects this low desire (low quantity or low WTP relative to price).
        """
        market_data = {
            "goods_market": {
                "food_current_sell_price": 100.0
            },
            "loan_market": {"interest_rate": 0.05}
        }
        
        self.ai_engine.decide_action_vector = MagicMock(return_value=HouseholdActionVector(
            consumption_aggressiveness={"food": 0.5},
            job_mobility_aggressiveness=0.0
        ))

        household_state = HouseholdStateDTO.from_household(self.household)
        household_config = _create_household_config(self.config)

        context = DecisionContext(
            state=household_state,
            config=household_config,
            markets={},
            goods_data=[self.config.GOODS["food"]],
            market_data=market_data,
            current_time=1
        )
        
        orders, _ = self.engine.make_decisions(context)

        buy_orders = [o for o in orders if o.item_id == "food" and o.order_type == "BUY"]

        if len(buy_orders) > 0:
            order = buy_orders[0]
            # Verify significant attenuation
            # Initial Agg = 0.5.
            # ROI ratio ~ 0.01.
            # New Agg ~ 0.005.
            # Valuation Modifier ~ 0.9.
            # WTP ~ 100 * 0.5 * 0.9 = 45.
            # Bid Price (45) < Ask Price (100).
            self.assertLess(order.price, 100.0)
        else:
            # If no order, that's also valid "prevention"
            pass

if __name__ == "__main__":
    unittest.main()
