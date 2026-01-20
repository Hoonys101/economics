import pytest
import random
from unittest.mock import MagicMock
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.core_agents import Household
from simulation.models import Talent
from simulation.ai.api import Personality
from simulation.ai.household_ai import HouseholdAI
from simulation.ai.ai_training_manager import AITrainingManager
from simulation.ai.q_table_manager import QTableManager

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
    ensure_config(golden_config, 'MITOSIS_Q_TABLE_MUTATION_RATE', 0.05)
    ensure_config(golden_config, 'IMITATION_MUTATION_RATE', 0.1)
    ensure_config(golden_config, 'IMITATION_MUTATION_MAGNITUDE', 0.05)
    ensure_config(golden_config, 'MITOSIS_MUTATION_PROBABILITY', 0.2)
    ensure_config(golden_config, 'EDUCATION_SENSITIVITY', 0.1)
    ensure_config(golden_config, 'BASE_LEARNING_RATE', 0.1)
    ensure_config(golden_config, 'MAX_LEARNING_RATE', 0.5)

def create_real_household_from_golden(mock_h, golden_config):
    # Use Talent from models, default if necessary
    talent = Talent(base_learning_rate=0.5, max_potential={})

    # Simple goods data
    goods_data = [{"id": "food"}, {"id": "housing"}]

    # Default personality/orientation if not on mock
    personality = getattr(mock_h, 'personality', Personality.MISER)
    if isinstance(personality, MagicMock):
         personality = Personality.MISER

    value_orientation = getattr(mock_h, 'value_orientation', "wealth")
    if isinstance(value_orientation, MagicMock):
        value_orientation = "wealth"

    # Handle numeric/primitive fields safely from MagicMock
    initial_assets = mock_h.assets if not isinstance(mock_h.assets, MagicMock) else 1000.0
    initial_needs = mock_h.needs if not isinstance(mock_h.needs, MagicMock) else {"survival": 0.5}
    initial_age = mock_h.age if hasattr(mock_h, 'age') and not isinstance(mock_h.age, MagicMock) else 25

    # Pre-configure Mock Engine
    mock_engine = MagicMock(spec=AIDrivenHouseholdDecisionEngine)
    mock_ai_engine = MagicMock()
    mock_engine.ai_engine = mock_ai_engine
    mock_shared_ai = MagicMock()
    mock_ai_engine.ai_decision_engine = mock_shared_ai

    # Default attributes for AI engine to pass clone checks
    mock_ai_engine.gamma = 0.9
    mock_ai_engine.base_alpha = 0.1
    mock_ai_engine.learning_focus = 0.5
    mock_action_selector = MagicMock()
    mock_action_selector.epsilon = 0.1
    mock_ai_engine.action_selector = mock_action_selector

    # Ensure loan_market exists (set to None)
    mock_engine.loan_market = None

    real_household = Household(
        id=mock_h.id if not isinstance(mock_h.id, MagicMock) else 1,
        talent=talent,
        goods_data=goods_data,
        initial_assets=float(initial_assets),
        initial_needs=dict(initial_needs) if isinstance(initial_needs, dict) else {"survival": 0.5},
        decision_engine=mock_engine,
        value_orientation=value_orientation,
        personality=personality,
        config_module=golden_config,
        initial_age=float(initial_age),
        gender="M",
    )

    if hasattr(mock_h, 'inventory') and not isinstance(mock_h.inventory, MagicMock):
        real_household.inventory = dict(mock_h.inventory)

    return real_household

def test_mitosis_zero_sum_logic(golden_config, golden_households):
    """
    CRITICAL: Verify Zero-Sum Asset Logic.
    Ensures that when a child is created with parent's assets, the total assets in the system remain constant.
    """
    setup_golden_config(golden_config)
    # Use first household from golden fixtures, or fallback if empty
    mock_h = golden_households[0] if golden_households else MagicMock()

    parent = create_real_household_from_golden(mock_h, golden_config)
    parent.assets = 10000.0
    initial_total_assets = parent.assets

    # Simulate Mitosis (DemographicManager logic)
    # 1. Determine split amount (e.g., 50% for fission, or 10% for birth)
    split_amount = parent.assets * 0.5

    # 2. Deduct from parent
    parent.assets -= split_amount

    # 3. Create child with deducted amount
    child = parent.clone(new_id=999, initial_assets_from_parent=split_amount, current_tick=100)

    # Assertions
    assert child.assets == split_amount
    assert parent.assets == initial_total_assets - split_amount
    assert parent.assets + child.assets == initial_total_assets
    assert child.id == 999

def test_mitosis_stock_inheritance(golden_config, golden_households):
    """
    CRITICAL: Verify Stock Inheritance Logic.
    Since `clone` does not automatically copy shares, this test verifies that
    Households CAN support share inheritance if the manager orchestrates it.
    """
    setup_golden_config(golden_config)
    mock_h = golden_households[0] if golden_households else MagicMock()
    parent = create_real_household_from_golden(mock_h, golden_config)

    # Setup Shares
    firm_1_id = 101
    firm_2_id = 102
    parent.shares_owned = {firm_1_id: 10, firm_2_id: 8}

    # Create Child (Vanilla Clone)
    child = parent.clone(new_id=999, initial_assets_from_parent=0, current_tick=100)

    # Verify Child starts empty (default behavior of clone)
    assert child.shares_owned == {}

    # Simulate Inheritance (Manager Logic)
    # Split shares 50/50
    # Note: shares_owned property returns a copy in Facade refactoring, so we must set it back.
    parent_shares = parent.shares_owned
    child_shares = child.shares_owned
    for firm_id, quantity in parent_shares.items():
        child_share = quantity // 2
        parent_shares[firm_id] -= child_share
        child_shares[firm_id] = child_share

    parent.shares_owned = parent_shares
    child.shares_owned = child_shares

    # Verify Distribution
    assert parent.shares_owned[firm_1_id] == 5
    assert child.shares_owned[firm_1_id] == 5
    assert parent.shares_owned[firm_2_id] == 4
    assert child.shares_owned[firm_2_id] == 4

    # Verify Total Shares Conserved
    assert parent.shares_owned[firm_1_id] + child.shares_owned[firm_1_id] == 10

def test_mitosis_brain_inheritance(golden_config, golden_households):
    """
    CRITICAL: Verify Q-Table and Brain Inheritance.
    Uses AITrainingManager to perform the brain transfer and validates Q-table content.
    """
    setup_golden_config(golden_config)
    mock_h = golden_households[0] if golden_households else MagicMock()
    parent = create_real_household_from_golden(mock_h, golden_config)

    # Setup Parent AI with specific knowledge
    mock_shared_ai = MagicMock()
    parent_ai = HouseholdAI(
        agent_id=str(parent.id),
        ai_decision_engine=mock_shared_ai,
        gamma=0.9
    )
    # Populate Q-Table
    parent_ai.q_consumption["food"] = QTableManager()
    # (State) -> [Action Values] (QTableManager expects Dict)
    test_state = (0, 0, 0, 0)
    test_values = {0: 1.0, 1: 0.5, 2: 0.1}
    parent_ai.q_consumption["food"].q_table = {test_state: test_values}

    parent_decision = AIDrivenHouseholdDecisionEngine(parent_ai, golden_config)
    # Fix: Ensure loan_market is set on the Real engine
    parent_decision.loan_market = None

    parent.decision_engine = parent_decision

    # Create Child
    child = parent.clone(new_id=999, initial_assets_from_parent=0, current_tick=100)

    # Setup Child AI (clone creates AIDrivenHouseholdDecisionEngine but we need to ensure structure for inheritance)
    # Clone logic calls _create_new_decision_engine which creates a fresh AI.
    # We rely on AITrainingManager to transfer knowledge.

    training_manager = AITrainingManager(agents=[parent, child], config_module=golden_config)
    training_manager.inherit_brain(parent, child)

    child_ai = child.decision_engine.ai_engine

    # Verify Q-Table Existence
    assert "food" in child_ai.q_consumption
    child_q_table = child_ai.q_consumption["food"].q_table
    assert test_state in child_q_table

    # Verify Values (Likely Mutated)
    child_values = child_q_table[test_state]
    assert len(child_values) == len(test_values)

    # Check that values are close but potentially mutated
    # Mutation magnitude is 0.05
    # Since keys are same
    for k in test_values:
        p_val = test_values[k]
        c_val = child_values[k]
        assert abs(p_val - c_val) <= 0.1 # Allow small margin for mutation + float error

    # Verify Personality (Inheritance or Mutation)
    assert isinstance(child.personality, Personality)
