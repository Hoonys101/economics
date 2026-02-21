import pytest
from unittest.mock import MagicMock
from simulation.decisions.household.consumption_manager import ConsumptionManager
from simulation.decisions.household.api import ConsumptionContext
from simulation.models import Order
from simulation.schemas import HouseholdActionVector
from simulation.ai.household_ai import HouseholdAI
from modules.system.api import DEFAULT_CURRENCY

@pytest.fixture
def mock_household():
    household = MagicMock()
    household.id = 100
    household.assets = {DEFAULT_CURRENCY: 10000}
    household.inventory = {}
    household.needs = {'survival': 10, 'comfort': 10}
    household.perceived_prices = {}
    household.demand_elasticity = 1.0
    household.conformity = 0.5
    return household

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.goods = {
        'food': {
            'utility_effects': {'survival': 10},
            'initial_price': 100,
            'is_veblen': False,
            'is_durable': False
        }
    }
    config.budget_limit_normal_ratio = 0.5
    config.budget_limit_urgent_ratio = 0.8
    config.budget_limit_urgent_need = 80
    config.market_price_fallback = 100
    config.max_willingness_to_pay_multiplier = 2.0
    config.min_purchase_quantity = 0.1
    return config

@pytest.fixture
def consumption_manager():
    return ConsumptionManager()

def test_consumption_manager_debt_constraint(consumption_manager, mock_household, mock_config):
    """Verify that debt_penalty < 1.0 reduces consumption."""

    market_data = {
        'goods_market': {'food_current_sell_price': 100}
    }
    action_vector = HouseholdActionVector(consumption_aggressiveness={'food': 1.0})

    # Ensure budget is the constraint.
    # Set household assets low enough.
    # Budget normal ratio 0.5.
    # Price ~100.
    # If assets=200 -> Budget=100. Qty=1.
    mock_household.assets = {DEFAULT_CURRENCY: 200}

    # 1. Base Case: No Debt Penalty (1.0)
    context_normal = ConsumptionContext(
        household=mock_household,
        config=mock_config,
        market_data=market_data,
        action_vector=action_vector,
        savings_roi=1.0,
        debt_penalty=1.0,
        stress_config=None,
        logger=None
    )

    orders_normal = consumption_manager.decide_consumption(context_normal)
    assert len(orders_normal) == 1
    qty_normal = orders_normal[0].quantity

    # 2. Stress Case: High Debt Penalty (0.5)
    # Budget should become 100 * 0.5 = 50.
    # Price 100 (actually bid_price might be higher ~105).
    # Qty should be ~0.5 (rounded or float).
    context_stress = ConsumptionContext(
        household=mock_household,
        config=mock_config,
        market_data=market_data,
        action_vector=action_vector,
        savings_roi=1.0,
        debt_penalty=0.5,
        stress_config=None,
        logger=None
    )

    orders_stress = consumption_manager.decide_consumption(context_stress)
    assert len(orders_stress) == 1
    qty_stress = orders_stress[0].quantity

    assert qty_stress < qty_normal
    assert qty_stress <= qty_normal * 0.5 + 0.1 # Allowance for float logic

def test_household_ai_debt_penalty_reward():
    """Verify that high DSR reduces reward."""
    # We need to mock AIDecisionEngine passed to HouseholdAI
    mock_engine = MagicMock()
    mock_engine.config_module.dsr_critical_threshold = 0.4
    mock_engine.config_module.ENABLE_VANITY_SYSTEM = False
    mock_engine.config_module.LEISURE_WEIGHT = 0.3

    ai = HouseholdAI(agent_id=100, ai_decision_engine=mock_engine)

    pre_state = {'needs': {'survival': 10}, 'assets': {DEFAULT_CURRENCY: 1000}}
    post_state = {'needs': {'survival': 10}, 'assets': {DEFAULT_CURRENCY: 1000}} # No change
    agent_data = {'current_wage': 10, 'assets': {DEFAULT_CURRENCY: 1000}, 'social_rank': 0.5, 'conformity': 0.5}

    # Case 1: Low Debt (No Penalty)
    market_data_low = {
        'debt_data': {
            100: {'daily_interest_burden': 0.0} # DSR = 0
        }
    }

    reward_low = ai._calculate_reward(pre_state, post_state, agent_data, market_data_low)

    # Case 2: High Debt (Penalty)
    # Wage 10. Assets 1000 (1% = 10). Income proxy = 10.
    # Threshold 0.4 -> burden > 4.0 triggers penalty.
    # Let's set burden = 8.0 (DSR 0.8)
    market_data_high = {
        'debt_data': {
            100: {'daily_interest_burden': 8.0}
        }
    }

    reward_high = ai._calculate_reward(pre_state, post_state, agent_data, market_data_high)

    assert reward_high < reward_low
    # DSR 0.8 vs 0.4 threshold -> excess 0.4. Penalty = 0.4 * 500 = 200.
    assert reward_high <= reward_low - 199.0
