import pytest
from unittest.mock import Mock, MagicMock, patch
from simulation.initialization.initializer import SimulationInitializer
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.ai_model import AIEngineRegistry
from simulation.metrics.economic_tracker import EconomicIndicatorTracker
from simulation.models import Talent
from simulation.ai.api import Personality

# Mock Config Module
@pytest.fixture
def mock_config_module():
    mock_config = Mock()
    mock_config.INITIAL_BANK_ASSETS = 100000.0
    mock_config.INITIAL_PROPERTY_VALUE = 1000.0
    mock_config.INITIAL_RENT_PRICE = 10.0
    mock_config.NUM_HOUSING_UNITS = 10
    mock_config.GOODS = {"food": {"initial_price": 10.0}}
    mock_config.FIRM_MIN_PRODUCTION_TARGET = 10.0
    mock_config.LIQUIDITY_NEED_INCREASE_RATE = 0.1
    mock_config.INITIAL_FIRM_LIQUIDITY_NEED = 100.0
    mock_config.VALUE_ORIENTATION_MAPPING = {}
    mock_config.PROFIT_HISTORY_TICKS = 10
    mock_config.STOCK_MARKET_ENABLED = False
    mock_config.TICKS_PER_YEAR = 100.0
    mock_config.INITIAL_BASE_ANNUAL_RATE = 0.05
    # Add attributes required by Bootstrapper
    mock_config.BOOTSTRAPPER_ENABLED = True
    # For tracker
    mock_config.TAX_BRACKETS = []
    mock_config.TAX_RATE_BASE = 0.1

    # Central Bank Config
    mock_config.CB_UPDATE_INTERVAL = 10
    mock_config.CB_INFLATION_TARGET = 0.02
    mock_config.CB_TAYLOR_ALPHA = 1.5
    mock_config.CB_TAYLOR_BETA = 0.5

    # Planner / System Configs
    mock_config.CHILD_MONTHLY_COST = 500.0
    mock_config.INFLATION_MEMORY_WINDOW = 10
    mock_config.QUALITY_SENSITIVITY_MEAN = 0.5
    mock_config.MARKETING_DECAY_RATE = 0.8
    mock_config.MARKETING_EFFICIENCY = 0.01
    mock_config.INITIAL_HOUSEHOLD_ASSETS_MEAN = 5000.0
    mock_config.STARTUP_COST = 30000.0
    mock_config.EXPECTED_STARTUP_ROI = 0.15
    mock_config.HOUSEHOLD_MIN_ASSETS_FOR_INVESTMENT = 1000.0
    mock_config.STOCK_INVESTMENT_EQUITY_DELTA_THRESHOLD = 0.1
    mock_config.STOCK_INVESTMENT_DIVERSIFICATION_COUNT = 5
    mock_config.DEBT_REPAYMENT_RATIO = 0.1
    mock_config.DEBT_REPAYMENT_CAP = 1000.0
    mock_config.DEBT_LIQUIDITY_RATIO = 0.5

    mock_config.OPPORTUNITY_COST_FACTOR = 0.3
    mock_config.EDUCATION_COST_MULTIPLIERS = {0: 1.0, 1: 1.5}
    mock_config.EDUCATION_WEALTH_THRESHOLDS = {0: 0, 1: 1000}
    mock_config.INITIAL_WAGE = 10.0

    return mock_config

@pytest.fixture
def mock_logger():
    return MagicMock()

@pytest.fixture
def mock_repository():
    repo = MagicMock()
    repo.save_simulation_run.return_value = 123
    return repo

@pytest.fixture
def mock_ai_trainer():
    return Mock(spec=AIEngineRegistry)

@pytest.fixture
def mock_agents(mock_config_module):
    # Households
    h1 = Mock(spec=Household)
    h1.id = 1
    h1.assets = 500.0
    h1.is_active = True
    h1.value_orientation = "test"
    h1.decision_engine = Mock()
    h1.needs = {"survival": 50.0, "liquidity_need": 10.0}
    h1.inventory = {}
    h1.owned_properties = []
    h1.config_module = mock_config_module
    h1.update_needs = Mock()

    h2 = Mock(spec=Household)
    h2.id = 2
    h2.assets = 300.0
    h2.is_active = True
    h2.value_orientation = "test"
    h2.decision_engine = Mock()
    h2.needs = {"survival": 50.0, "liquidity_need": 10.0}
    h2.inventory = {}
    h2.owned_properties = []
    h2.config_module = mock_config_module
    h2.update_needs = Mock()

    # Firms
    f1 = Mock(spec=Firm)
    f1.id = 101
    f1.assets = 1000.0
    f1.is_active = True
    f1.specialization = "food"
    f1.decision_engine = Mock()
    f1.inventory = {"food": 10}
    f1.input_inventory = {}
    f1.needs = {"liquidity_need": 100.0}
    f1.hr = Mock()
    f1.hr.employees = []
    f1.finance = Mock()
    f1.finance.balance = 1000.0
    f1.config_module = mock_config_module
    f1.update_needs = Mock()
    # Bootstrapper calls _add_assets
    f1._add_assets = Mock(side_effect=lambda x: setattr(f1, 'assets', f1.assets + x))
    f1.production_target = 100.0 # for inject_initial_liquidity
    # FirmSystem needs
    f1.get_financial_snapshot.return_value = {"total_assets": 1000.0}

    return [h1, h2], [f1]

def test_verify_td_115_and_111(mock_config_module, mock_logger, mock_repository, mock_ai_trainer, mock_agents):
    households, firms = mock_agents

    # Mock ConfigManager
    mock_config_manager = Mock()
    mock_config_manager.get.return_value = 0.05

    initializer = SimulationInitializer(
        config_manager=mock_config_manager,
        config_module=mock_config_module,
        goods_data=[{"id": "food"}],
        repository=mock_repository,
        logger=mock_logger,
        households=households,
        firms=firms,
        ai_trainer=mock_ai_trainer
    )

    # Patch Bootstrapper to verify order and avoid side effects (or we can let it run if we mock enough)
    # We patch it to verify calls
    with patch("simulation.initialization.initializer.Bootstrapper") as MockBootstrapper:
        sim = initializer.build_simulation()

        # Verify Bootstrapper order: inject then assign
        # In python 3.7+ call order is preserved in method_calls
        # but method_calls on the class mock might collect calls to children

        print("\nBootstrapper Calls:")
        for call in MockBootstrapper.method_calls:
            print(call)

        # Expected: inject_initial_liquidity, then force_assign_workers
        assert MockBootstrapper.inject_initial_liquidity.called
        assert MockBootstrapper.force_assign_workers.called

        # Verify TD-115: Baseline Money Supply
        assert hasattr(sim.world_state, "baseline_money_supply")
        baseline = sim.world_state.baseline_money_supply
        print(f"Baseline Money Supply: {baseline}")
        assert baseline > 0

        # Verify TD-111: M2 Calculation (Exclude Reflux)
        # Setup Reflux with some balance
        sim.reflux_system.balance = 999.0

        # Calculate Total (Integrity Check - Includes Reflux)
        total_integrity = sim.world_state.calculate_total_money()

        # Calculate M2 (Reporting - Excludes Reflux)
        m2 = sim.tracker.get_m2_money_supply(sim.world_state)

        print(f"Total Integrity: {total_integrity}")
        print(f"M2: {m2}")
        print(f"Reflux: {sim.reflux_system.balance}")

        assert total_integrity == m2 + sim.reflux_system.balance
        assert m2 < total_integrity

        # Recalculate what baseline was supposed to be
        # H1(500) + H2(300) + F1(1000) + Bank(100000) + Gov(0) = 101800
        # Reflux was 0 at init.
        assert baseline == 101800.0
