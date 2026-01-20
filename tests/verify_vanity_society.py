import pytest
from unittest.mock import Mock
import sys
import os

# Adjust path to include the root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulation.core_agents import Household
from simulation.ai.enums import Personality
from simulation.decisions.housing_manager import HousingManager
from simulation.ai.household_ai import HouseholdAI
import config

@pytest.fixture
def vanity_config():
    config_module = Mock(spec=config)
    # Setup basic config
    config_module.ENABLE_VANITY_SYSTEM = True
    config_module.VANITY_WEIGHT = 1.0
    config_module.REFERENCE_GROUP_PERCENTILE = 0.2
    config_module.CONFORMITY_RANGES = {
        "STATUS_SEEKER": (0.8, 0.9),
        "MISER": (0.1, 0.2)
    }
    config_module.GOODS = {
        "luxury_bag": {"is_veblen": True}
    }
    config_module.MIMICRY_FACTOR = 0.5
    config_module.INITIAL_RENT_PRICE = 100.0
    config_module.MAINTENANCE_RATE_PER_TICK = 0.001
    config_module.DSR_CRITICAL_THRESHOLD = 0.4
    config_module.HOUSEHOLD_MAX_PURCHASE_QUANTITY = 5.0
    config_module.BULK_BUY_NEED_THRESHOLD = 70.0
    config_module.BULK_BUY_AGG_THRESHOLD = 0.8
    config_module.BULK_BUY_MODERATE_RATIO = 0.6
    config_module.NEED_FACTOR_BASE = 0.5
    config_module.NEED_FACTOR_SCALE = 100.0
    config_module.VALUATION_MODIFIER_BASE = 0.9
    config_module.VALUATION_MODIFIER_RANGE = 0.2
    config_module.MARKET_PRICE_FALLBACK = 10.0
    config_module.MIN_PURCHASE_QUANTITY = 0.1
    config_module.BUDGET_LIMIT_NORMAL_RATIO = 0.5
    config_module.BUDGET_LIMIT_URGENT_NEED = 80.0
    config_module.BUDGET_LIMIT_URGENT_RATIO = 0.9
    config_module.JOB_QUIT_THRESHOLD_BASE = 2.0
    config_module.JOB_QUIT_PROB_BASE = 0.1
    config_module.JOB_QUIT_PROB_SCALE = 0.9
    config_module.RESERVATION_WAGE_BASE = 1.5
    config_module.RESERVATION_WAGE_RANGE = 1.0
    config_module.LABOR_MARKET_MIN_WAGE = 8.0
    config_module.TARGET_FOOD_BUFFER_QUANTITY = 5.0
    config_module.PANIC_BUYING_THRESHOLD = 0.05
    config_module.DEFLATION_WAIT_THRESHOLD = -0.05
    config_module.HOARDING_FACTOR = 0.5
    config_module.DELAY_FACTOR = 0.5
    config_module.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 2.0
    config_module.STOCK_MARKET_ENABLED = False
    config_module.HOUSEHOLD_MIN_ASSETS_FOR_INVESTMENT = 500.0
    config_module.HOUSEHOLD_INVESTMENT_BUDGET_RATIO = 0.2
    config_module.STOCK_MIN_ORDER_QUANTITY = 1.0
    config_module.STOCK_BUY_DISCOUNT_THRESHOLD = 0.1
    config_module.STOCK_SELL_PROFIT_THRESHOLD = 0.15
    config_module.STARTUP_COST = 30000.0
    config_module.EXPECTED_STARTUP_ROI = 0.15
    config_module.WAGE_RECOVERY_RATE = 0.01

    return config_module

def test_social_rank_calculation(vanity_config):
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

    # Inject the logic here to test correctness
    scores = []
    hm = HousingManager(None, vanity_config)
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

    assert ranks[4] == 1.0 # Top
    assert ranks[0] == 1.0 - (4/5) # 0.2 (Bottom)
    assert ranks[3] > ranks[2]

def test_veblen_demand(vanity_config):
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
    household.wage_modifier = 1.0 # Added to fix AttributeError
    household.get_agent_data.return_value = {"assets": 10000.0, "needs": {"social": 10.0}, "inventory": {}}

    ai_engine = Mock()
    # Mock action vector
    from simulation.schemas import HouseholdActionVector
    ai_engine.decide_action_vector.return_value = HouseholdActionVector(
        consumption_aggressiveness={"luxury_bag": 0.5}
    )

    engine = AIDrivenHouseholdDecisionEngine(ai_engine, vanity_config)

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

    # Just ensure code execution path
    assert len(orders_high) > 0
    assert wtp_high > wtp_low

def test_mimicry_trigger(vanity_config):
    """Verify panic buy trigger"""
    agent = Mock(spec=Household)
    agent.conformity = 1.0
    agent.is_homeless = True # Tier 0
    agent.residing_property_id = None

    config = vanity_config
    hm = HousingManager(agent, config)

    # Ref Standard: Tier 1.0
    ref = {"avg_housing_tier": 1.0}

    # Case A: Urgency 0.5 (Borderline) -> None
    intent = hm.decide_mimicry_purchase(ref)
    assert intent is None

    # Case B: Increase Gap or Conformity? Conformity maxed.
    # Increase Mimicry Factor in config
    config.MIMICRY_FACTOR = 0.6
    hm = HousingManager(agent, config)

    intent = hm.decide_mimicry_purchase(ref)
    assert intent is not None
    assert intent.priority == "URGENT"
    assert intent.max_ltv == 0.95

def test_vanity_switch_ab(vanity_config):
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
    vanity_config.VANITY_WEIGHT = 0.0

    ai = HouseholdAI("agent_1", Mock(), 0.9, 0.1, 0.1, 0.5)
    # Mock the ai_decision_engine.config_module
    decision_engine_mock = Mock()
    decision_engine_mock.config_module = vanity_config
    ai.ai_decision_engine = decision_engine_mock
    # Mock LEISURE_WEIGHT access from config if needed, but it's used inside
    vanity_config.LEISURE_WEIGHT = 0.3

    reward_a = ai._calculate_reward(pre_state, post_state, agent_data, market_data)

    # Scenario B: Vanity Enabled (WEIGHT = 1.5)
    vanity_config.VANITY_WEIGHT = 1.5
    reward_b = ai._calculate_reward(pre_state, post_state, agent_data, market_data)

    # Reward A should be 0.0 (No asset change, no need change, no vanity)
    # Reward B should be negative
    assert reward_a == 0.0
    assert reward_b < 0.0
    assert reward_b == pytest.approx(-45.0, abs=1.0)
