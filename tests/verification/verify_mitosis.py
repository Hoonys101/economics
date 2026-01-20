import pytest
from unittest.mock import MagicMock
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.core_agents import Household, Talent
from simulation.ai.api import Personality
from simulation.ai.household_ai import HouseholdAI

# Helper to force set primitive config
def ensure_config(golden_config, key, value):
    if not hasattr(golden_config, key) or isinstance(getattr(golden_config, key), MagicMock):
        setattr(golden_config, key, value)

def setup_golden_config(golden_config):
    ensure_config(golden_config, 'INFLATION_MEMORY_WINDOW', 10)
    ensure_config(golden_config, 'TICKS_PER_YEAR', 100)
    ensure_config(golden_config, 'VALUE_ORIENTATION_MAPPING', {})
    ensure_config(golden_config, 'ADAPTATION_RATE_IMPULSIVE', 0.5)
    ensure_config(golden_config, 'ADAPTATION_RATE_CONSERVATIVE', 0.1)
    ensure_config(golden_config, 'ADAPTATION_RATE_NORMAL', 0.2)
    ensure_config(golden_config, 'PERCEIVED_PRICE_UPDATE_FACTOR', 0.1)
    ensure_config(golden_config, 'INITIAL_HOUSEHOLD_ASSETS_MEAN', 1000.0)
    ensure_config(golden_config, 'CONFORMITY_RANGES', {})
    ensure_config(golden_config, 'EDUCATION_WEALTH_THRESHOLDS', {0: 0, 1: 1000, 2: 5000})
    ensure_config(golden_config, 'EDUCATION_COST_MULTIPLIERS', {0: 1.0, 1: 1.2, 2: 1.5})
    ensure_config(golden_config, 'INITIAL_WAGE', 10.0)
    ensure_config(golden_config, 'QUALITY_PREF_SNOB_MIN', 0.7)
    ensure_config(golden_config, 'QUALITY_PREF_MISER_MAX', 0.3)
    ensure_config(golden_config, 'HOUSEHOLD_MIN_WAGE_DEMAND', 6.0)

def create_real_household_from_golden(mock_h, golden_config):
    # 1. Talent (Not in golden snapshot, use default)
    talent = Talent(base_learning_rate=0.5, max_potential={})

    # 2. Goods Data
    goods_data = [{"id": "food"}, {"id": "housing"}]

    # 3. Personality & Value Orientation
    personality = Personality.MISER
    value_orientation = "wealth"

    # 4. Extract data
    initial_assets = mock_h.assets if not isinstance(mock_h.assets, MagicMock) else 1000.0
    initial_needs = mock_h.needs if not isinstance(mock_h.needs, MagicMock) else {"survival": 0.5}
    initial_age = mock_h.age if hasattr(mock_h, 'age') and not isinstance(mock_h.age, MagicMock) else 25

    real_household = Household(
        id=mock_h.id if not isinstance(mock_h.id, MagicMock) else 1,
        talent=talent,
        goods_data=goods_data,
        initial_assets=float(initial_assets),
        initial_needs=dict(initial_needs),
        decision_engine=MagicMock(spec=AIDrivenHouseholdDecisionEngine),
        value_orientation=value_orientation,
        personality=personality,
        config_module=golden_config,
        initial_age=float(initial_age),
        gender="M",
    )

    if hasattr(mock_h, 'inventory') and not isinstance(mock_h.inventory, MagicMock):
        real_household.inventory = dict(mock_h.inventory)

    return real_household

def test_mitosis_stage1(golden_config, golden_households):
    """
    Stage 1: Golden Config Only
    - Replace Config mock with golden_config.
    - Keep DecisionEngine as MagicMock.
    - Validate that Household.clone() works with complex golden data.
    """
    setup_golden_config(golden_config)
    mock_h = golden_households[0]
    real_household = create_real_household_from_golden(mock_h, golden_config)

    # Stage 1 Mock Decision Engine
    mock_engine = MagicMock(spec=AIDrivenHouseholdDecisionEngine)
    mock_ai_engine = MagicMock()
    mock_engine.ai_engine = mock_ai_engine
    mock_shared_ai = MagicMock()
    mock_ai_engine.ai_decision_engine = mock_shared_ai
    mock_ai_engine.gamma = 0.9
    mock_ai_engine.base_alpha = 0.1
    mock_ai_engine.learning_focus = 0.5
    mock_action_selector = MagicMock()
    mock_action_selector.epsilon = 0.1
    mock_ai_engine.action_selector = mock_action_selector
    mock_engine.loan_market = None

    real_household.decision_engine = mock_engine

    # Test clone logic
    new_id = 999
    initial_assets_child = real_household.assets / 2.0
    current_tick = 100

    child_household = real_household.clone(new_id, initial_assets_child, current_tick)

    assert child_household is not None
    assert isinstance(child_household, Household)
    assert child_household.id == new_id
    assert abs(child_household.assets - initial_assets_child) < 1e-6
    assert isinstance(child_household.decision_engine, AIDrivenHouseholdDecisionEngine)


def test_mitosis_stage2(golden_config, golden_households):
    """
    Stage 2: Real DecisionEngine
    - Use real DecisionEngine with real HouseholdAI.
    - Isolate failures to engine instantiation/cloning logic.
    """
    setup_golden_config(golden_config)
    mock_h = golden_households[0]
    real_household = create_real_household_from_golden(mock_h, golden_config)

    # ---------------------------------------------------------
    # Setup Real Decision Engine
    # ---------------------------------------------------------
    mock_shared_ai_engine = MagicMock() # Global engine can be mocked

    real_ai_engine = HouseholdAI(
        agent_id=str(real_household.id),
        ai_decision_engine=mock_shared_ai_engine,
        gamma=0.9,
        epsilon=0.1,
        base_alpha=0.1,
        learning_focus=0.5
    )

    real_decision_engine = AIDrivenHouseholdDecisionEngine(
        ai_engine=real_ai_engine,
        config_module=golden_config,
        logger=real_household.logger
    )
    # Inject dependencies that might be needed
    real_decision_engine.loan_market = MagicMock()

    real_household.decision_engine = real_decision_engine

    # ---------------------------------------------------------
    # Test clone logic with real engine
    # ---------------------------------------------------------
    new_id = 888
    initial_assets_child = real_household.assets / 2.0
    current_tick = 200

    child_household = real_household.clone(new_id, initial_assets_child, current_tick)

    # Verify clone success
    assert child_household is not None
    assert child_household.id == new_id
    assert abs(child_household.assets - initial_assets_child) < 1e-6

    # Verify Engine Cloning
    assert isinstance(child_household.decision_engine, AIDrivenHouseholdDecisionEngine)
    assert child_household.decision_engine is not real_decision_engine

    # Verify AI Cloning
    child_ai = child_household.decision_engine.ai_engine
    assert isinstance(child_ai, HouseholdAI)
    assert child_ai.agent_id == str(new_id)
    assert child_ai.ai_decision_engine == mock_shared_ai_engine # Should share the same global engine

    # Verify Q-Table or state structure exists (basic check)
    assert hasattr(child_ai, 'q_consumption')
