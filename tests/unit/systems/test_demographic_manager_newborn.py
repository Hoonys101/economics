import pytest
from unittest.mock import MagicMock, PropertyMock

from simulation.systems.demographic_manager import DemographicManager
from simulation.core_agents import Household
from simulation.ai.enums import Personality

# [Test File Start]

@pytest.fixture
def mock_config():
    """Fixture to create a mock config object for testing."""
    config = MagicMock()

    # Define the expected config value for this test
    config.NEWBORN_INITIAL_NEEDS = {
        "survival": 60.0,
        "social": 20.0,
        "improvement": 10.0,
        "asset": 10.0,
        "imitation_need": 15.0,
        "labor_need": 0.0,
        "liquidity_need": 50.0
    }

    # Mock other required config values
    config.REPRODUCTION_AGE_START = 20
    config.REPRODUCTION_AGE_END = 45
    config.NEWBORN_ENGINE_TYPE = "AIDriven"
    config.MITOSIS_MUTATION_PROBABILITY = 0.1
    # Add other necessary config mocks as needed/discovered
    config.VALUE_ORIENTATION_MAPPING = {}
    config.SURVIVAL_NEED_CONSUMPTION_THRESHOLD = 0.8
    config.FOOD_PURCHASE_MAX_PER_TICK = 5.0
    config.ASSETS_THRESHOLD_FOR_OTHER_ACTIONS = 100.0
    config.LABOR_MARKET_MIN_WAGE = 5.0
    config.HOUSEHOLD_LOW_ASSET_THRESHOLD = 50.0
    config.HOUSEHOLD_LOW_ASSET_WAGE = 6.0
    config.HOUSEHOLD_DEFAULT_WAGE = 10.0
    config.MARKET_PRICE_FALLBACK = 1.0
    config.NEED_FACTOR_BASE = 1.0
    config.NEED_FACTOR_SCALE = 1.0
    config.VALUATION_MODIFIER_BASE = 1.0
    config.VALUATION_MODIFIER_RANGE = 0.1
    config.HOUSEHOLD_MAX_PURCHASE_QUANTITY = 5.0
    config.BULK_BUY_NEED_THRESHOLD = 0.9
    config.BULK_BUY_AGG_THRESHOLD = 0.8
    config.BULK_BUY_MODERATE_RATIO = 0.5
    config.DSR_CRITICAL_THRESHOLD = 0.8
    config.BUDGET_LIMIT_NORMAL_RATIO = 0.8
    config.BUDGET_LIMIT_URGENT_NEED = 0.9
    config.BUDGET_LIMIT_URGENT_RATIO = 0.9
    config.MIN_PURCHASE_QUANTITY = 0.1
    config.JOB_QUIT_THRESHOLD_BASE = 0.5
    config.JOB_QUIT_PROB_BASE = 0.1
    config.JOB_QUIT_PROB_SCALE = 0.1
    config.HOUSEHOLD_MIN_ASSETS_FOR_INVESTMENT = 500.0
    config.STOCK_INVESTMENT_EQUITY_DELTA_THRESHOLD = 0.1
    config.STOCK_INVESTMENT_DIVERSIFICATION_COUNT = 3
    config.DEBT_REPAYMENT_RATIO = 0.1
    config.DEBT_REPAYMENT_CAP = 100.0
    config.DEBT_LIQUIDITY_RATIO = 0.5
    config.INITIAL_RENT_PRICE = 50.0
    config.INITIAL_HOUSEHOLD_ASSETS_MEAN = 1000.0
    config.CONFORMITY_RANGES = {}
    config.QUALITY_PREF_MISER_MAX = 0.3
    config.QUALITY_PREF_SNOB_MIN = 0.7
    config.SOCIAL_STATUS_ASSET_WEIGHT = 0.5
    config.INITIAL_HOUSEHOLD_AGE_RANGE = (20, 50)
    config.INITIAL_APTITUDE_DISTRIBUTION = (0.5, 0.1) # Mean, StdDev for gauss
    config.PRICE_MEMORY_LENGTH = 10
    config.WAGE_MEMORY_LENGTH = 10
    config.TICKS_PER_YEAR = 100
    config.ADAPTATION_RATE_NORMAL = 0.1
    config.ADAPTATION_RATE_IMPULSIVE = 0.2
    config.ADAPTATION_RATE_CONSERVATIVE = 0.05
    config.PERCEIVED_PRICE_UPDATE_FACTOR = 0.1
    config.LEISURE_COEFFS = {}

    return config

@pytest.fixture
def mock_simulation():
    """Fixture to create a mock simulation 'God Object'."""
    sim = MagicMock()

    # Mock all attributes accessed by process_births
    sim.next_agent_id = 101
    sim.time = 1000
    sim.logger = MagicMock()

    # Mock dependent systems
    sim.ai_trainer = MagicMock()
    sim.ai_trainer.get_engine.return_value = MagicMock()
    sim.markets = {"loan_market": MagicMock()}
    sim.goods_data = [{"id": "food"}, {"id": "housing"}] # Assuming this is sufficient
    sim.settlement_system = MagicMock()

    # Mock the AI Training Manager for brain inheritance
    type(sim).ai_training_manager = PropertyMock(return_value=MagicMock())

    return sim

@pytest.fixture
def parent_agent(mock_config):
    """Fixture for a parent Household agent ready to give birth."""
    parent = MagicMock(spec=Household)
    parent.id = 1
    parent.age = 30
    parent.assets = 1000.0
    parent.talent = MagicMock()
    parent.personality = Personality.MISER
    parent.value_orientation = "TRADITIONAL"
    parent.risk_aversion = 0.5
    parent.generation = 1
    parent.children_ids = []

    # Mock methods
    # parent._sub_assets.return_value = None # Removed legacy method mock

    return parent

def test_newborn_receives_initial_needs_from_config(mock_config, mock_simulation, parent_agent):
    """
    VERIFY: A newborn household is initialized with 'initial_needs' from the
            mocked config, not a hardcoded default.
    """
    # ARRANGE
    # Instantiate the manager and surgically attach the mock config
    manager = DemographicManager(config_module=mock_config)
    manager.logger = MagicMock() # Isolate logger

    birth_requests = [parent_agent]

    # ACT
    # This now uses a completely mocked ecosystem
    new_children = manager.process_births(mock_simulation, birth_requests)

    # ASSERT
    if len(new_children) == 0:
        # Debugging helper: print logs if empty
        print(f"DEBUG: Logger calls: {manager.logger.method_calls}")

    assert len(new_children) == 1
    child = new_children[0]

    # The CRITICAL check: are the needs from our mock_config?
    assert child.needs == mock_config.NEWBORN_INITIAL_NEEDS
    assert "survival" in child.needs
    assert child.needs["survival"] == 60.0

    # Verify other attributes were set correctly
    assert child.id == 101
    assert child.parent_id == parent_agent.id
    assert child.age == 0.0

    # Verify asset transfer happened
    expected_gift = parent_agent.assets * 0.1
    # Check if transfer was called on the mock simulation's settlement system
    # Since we didn't inject into manager.settlement_system in this test (it's None),
    # the manager falls back to simulation.settlement_system (which is mock_simulation.settlement_system)
    mock_simulation.settlement_system.transfer.assert_called_once_with(
        parent_agent, child, expected_gift, "BIRTH_GIFT"
    )
