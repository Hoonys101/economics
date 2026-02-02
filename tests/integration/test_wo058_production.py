import pytest
from unittest.mock import Mock, MagicMock
from simulation.engine import Simulation
from simulation.systems.bootstrapper import Bootstrapper
from simulation.core_agents import Household, Talent
from simulation.firms import Firm
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
from simulation.ai.api import Personality
from simulation.metrics.economic_tracker import EconomicIndicatorTracker
from simulation.utils.config_factory import create_config_dto
from simulation.dtos.config_dtos import HouseholdConfigDTO, FirmConfigDTO
import config as global_config

@pytest.fixture
def mock_config():
    """Provides a mock config object with necessary definitions."""
    config = Mock()
    config.GOODS = {
        "food": {"inputs": {}},
        "tools": {"inputs": {"wood": 1}},
    }
    config.FIRM_MIN_PRODUCTION_TARGET = 10.0
    config.VALUE_ORIENTATION_MAPPING = {
        "test": {
            "preference_asset": 1.0,
            "preference_social": 1.0,
            "preference_growth": 1.0,
        }
    }
    # Add other necessary config attributes
    config.INITIAL_BANK_ASSETS = 1000000.0
    config.NUM_HOUSING_UNITS = 100
    config.INITIAL_PROPERTY_VALUE = 10000.0
    config.INITIAL_RENT_PRICE = 100.0
    config.STOCK_MARKET_ENABLED = False
    config.INFLATION_MEMORY_WINDOW = 10
    config.ADAPTATION_RATE_IMPULSIVE = 0.8
    config.ADAPTATION_RATE_CONSERVATIVE = 0.1
    config.ADAPTATION_RATE_NORMAL = 0.3
    config.TICKS_PER_YEAR = 100
    config.EDUCATION_WEALTH_THRESHOLDS = {}
    config.EDUCATION_LEVEL_DISTRIBUTION = [1.0]
    config.INITIAL_WAGE = 10.0
    config.EDUCATION_COST_MULTIPLIERS = {}
    config.CONFORMITY_RANGES = {
        "MISER": (0.1, 0.3),
        None: (0.3, 0.7)
    }
    config.INITIAL_HOUSEHOLD_ASSETS_MEAN = 5000.0
    config.QUALITY_PREF_MISER_MAX = 0.3
    config.PROFIT_HISTORY_TICKS = 10
    config.INITIAL_BASE_ANNUAL_RATE = 0.05
    config.CB_INFLATION_TARGET = 0.02
    config.BASE_DESIRE_GROWTH = 1.0
    config.MAX_DESIRE_VALUE = 100.0
    config.SURVIVAL_NEED_DEATH_THRESHOLD = 100.0
    config.ASSETS_DEATH_THRESHOLD = 0.0
    config.HOUSEHOLD_DEATH_TURNS_THRESHOLD = 4
    config.INVENTORY_HOLDING_COST_RATE = 0.01
    config.MARKETING_DECAY_RATE = 0.8
    config.MARKETING_EFFICIENCY = 0.01
    config.PERCEIVED_QUALITY_ALPHA = 0.2
    config.LIQUIDITY_NEED_INCREASE_RATE = 0.1
    config.ASSETS_CLOSURE_THRESHOLD = 0.0
    config.FIRM_CLOSURE_TURNS_THRESHOLD = 20
    config.CHILD_MONTHLY_COST = 500.0
    config.OPPORTUNITY_COST_FACTOR = 0.3
    config.CAPITAL_DEPRECIATION_RATE = 0.05
    config.AUTOMATION_LABOR_REDUCTION = 0.5
    config.LABOR_ALPHA = 0.7
    config.LABOR_ELASTICITY_MIN = 0.1
    return config

@pytest.fixture
def mock_repo():
    """Provides a mock repository object."""
    repo = MagicMock()
    repo.save_simulation_run.return_value = 1
    return repo

@pytest.fixture
def mock_ai_trainer():
    """Provides a mock AI trainer."""
    return Mock()

def test_bootstrapper_injection(mock_config, mock_repo, mock_ai_trainer):
    """Tests that the bootstrapper correctly injects capital and inputs."""
    hh_config_dto = create_config_dto(global_config, HouseholdConfigDTO)
    firm_config_dto = create_config_dto(global_config, FirmConfigDTO)

    talent = Talent(base_learning_rate=0.1, max_potential={})
    households = [Household(id=i, talent=talent, goods_data=[], initial_assets=1000, initial_needs={'survival': 0}, decision_engine=Mock(spec=AIDrivenHouseholdDecisionEngine), value_orientation="test", config_dto=hh_config_dto) for i in range(1)]
    firms = [
        Firm(id=100, initial_capital=500, specialization="tools", decision_engine=Mock(spec=AIDrivenFirmDecisionEngine), config_dto=firm_config_dto, value_orientation="Profit", initial_liquidity_need=100, productivity_factor=1),
        Firm(id=101, initial_capital=2500, specialization="food", decision_engine=Mock(spec=AIDrivenFirmDecisionEngine), config_dto=firm_config_dto, value_orientation="Profit", initial_liquidity_need=100, productivity_factor=1)
    ]

    # The bootstrapper is called during the Simulation initialization
    mock_config_manager = Mock()
    mock_config_manager.get.return_value = "test.db"
    sim = Simulation(config_manager=mock_config_manager, config_module=mock_config, logger=Mock(), repository=mock_repo)
    sim.world_state.households = households
    sim.world_state.firms = firms
    sim.world_state.ai_trainer = mock_ai_trainer
    sim.world_state.goods_data = []
    sim.world_state.tracker = EconomicIndicatorTracker(config_module=mock_config)

    Bootstrapper.inject_initial_liquidity(sim.firms, mock_config)
    Bootstrapper.force_assign_workers(sim.firms, sim.households)

    # Assert Assets >= 2000
    for firm in sim.firms:
        assert firm.assets >= 2000.0, f"Firm {firm.id} undercapitalized"

        # Assert Inputs Present
        if "inputs" in mock_config.GOODS[firm.specialization]:
            inputs = mock_config.GOODS[firm.specialization]["inputs"]
            for mat in inputs:
                assert firm.input_inventory.get(mat, 0) > 0, f"Firm {firm.id} missing input {mat}"

def test_production_kickstart(mock_config, mock_repo, mock_ai_trainer):
    """Tests that the economy starts and production is non-zero after bootstrapping."""
    hh_config_dto = create_config_dto(global_config, HouseholdConfigDTO)
    firm_config_dto = create_config_dto(global_config, FirmConfigDTO)

    talent = Talent(base_learning_rate=0.1, max_potential={})
    households = [Household(id=i, talent=talent, goods_data=[], initial_assets=1000, initial_needs={'survival': 0}, decision_engine=Mock(spec=AIDrivenHouseholdDecisionEngine), value_orientation="test", config_dto=hh_config_dto) for i in range(1)]
    firms = [
        Firm(id=100, initial_capital=3000, specialization="tools", decision_engine=Mock(spec=AIDrivenFirmDecisionEngine), config_dto=firm_config_dto, value_orientation="Profit", initial_liquidity_need=100, productivity_factor=1),
    ]

    # This is a simplified simulation setup; a real test would need more comprehensive mocks
    mock_config_manager = Mock()
    mock_config_manager.get.return_value = "test.db"
    sim = Simulation(config_manager=mock_config_manager, config_module=mock_config, logger=Mock(), repository=mock_repo)
    sim.world_state.households = households
    sim.world_state.firms = firms
    sim.world_state.ai_trainer = mock_ai_trainer
    sim.world_state.goods_data = []
    sim.world_state.tracker = EconomicIndicatorTracker(config_module=mock_config)

    Bootstrapper.inject_initial_liquidity(sim.firms, mock_config)
    Bootstrapper.force_assign_workers(sim.firms, sim.households)

    # We will manually trigger production to verify the bootstrapper's effect.
    firm = sim.firms[0]
    # To make produce work, we need to ensure the firm has employees
    mock_employee = households[0]
    firm.employees = [mock_employee]
    firm.hr.employees = [mock_employee]
    firm.input_inventory['wood'] = 100.0
    firm.productivity_factor = 1.0

    firm.produce(0) # Tick 0

    sim.tracker.track(1, sim.households, sim.firms, sim.markets, 0)

    # Assert Total Production > 0
    metrics = sim.tracker.get_latest_indicators()
    assert metrics['total_production'] > 0, "Economy is deadlocked!"
