import pytest
import sqlite3
import json
from unittest.mock import MagicMock, patch
from collections import deque, defaultdict

from simulation.initialization.initializer import SimulationInitializer
from simulation.db.repository import SimulationRepository
from simulation.db.schema import create_tables
from simulation.dtos.api import AgentStateData
from simulation.dtos.persistence import HouseholdPersistenceDTO, FirmPersistenceDTO
from simulation.utils.serializer import serialize_state
from modules.household.dtos import HouseholdSnapshotDTO, BioStateDTO, EconStateDTO, SocialStateDTO
from modules.firm.api import FirmSnapshotDTO, FinanceStateDTO, ProductionStateDTO, SalesStateDTO, HRStateDTO, FirmConfigDTO
from simulation.ai.enums import Personality
from modules.finance.wallet.wallet import Wallet
from simulation.portfolio import Portfolio
from simulation.models import Talent

@pytest.fixture
def in_memory_repo():
    conn = sqlite3.connect(":memory:")
    create_tables(conn)

    # Debug Schema
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(simulation_runs)")
    print(f"DEBUG SCHEMA simulation_runs: {cursor.fetchall()}")
    cursor.execute("PRAGMA table_info(agent_states)")
    print(f"DEBUG SCHEMA agent_states: {cursor.fetchall()}")

    # Inject connection directly
    repo = SimulationRepository(connection=conn)
    yield repo
    repo.close()
    conn.close()

def test_batch_load_from_db(in_memory_repo, mock_config, config_manager):
    # Setup Mock Config values required for Household Init
    mock_config.INITIAL_HOUSEHOLD_AGE_RANGE = (20, 60)
    mock_config.INITIAL_APTITUDE_DISTRIBUTION = (0.5, 0.1)
    mock_config.ELASTICITY_MAPPING = {}
    mock_config.VALUE_ORIENTATION_MAPPING = {}
    mock_config.CONFORMITY_RANGES = {}
    mock_config.LEISURE_COEFFS = {}
    mock_config.AGE_DEATH_PROBABILITIES = {}
    mock_config.EDUCATION_COST_MULTIPLIERS = {}

    # Add missing config values to prevent MagicMock leaking into logic
    mock_config.INITIAL_HOUSEHOLD_ASSETS_MEAN = 50000
    mock_config.QUALITY_PREF_SNOB_MIN = 0.8
    mock_config.QUALITY_PREF_MISER_MAX = 0.2
    mock_config.TICKS_PER_YEAR = 100
    mock_config.WAGE_MEMORY_LENGTH = 10
    mock_config.PRICE_MEMORY_LENGTH = 10
    mock_config.ADAPTATION_RATE_NORMAL = 0.1
    mock_config.ADAPTATION_RATE_IMPULSIVE = 0.2
    mock_config.ADAPTATION_RATE_CONSERVATIVE = 0.05
    mock_config.STARTUP_COST = 1000
    mock_config.LABOR_MARKET_MIN_WAGE = 10
    mock_config.HOUSEHOLD_LOW_ASSET_WAGE = 5
    mock_config.HOUSEHOLD_DEFAULT_WAGE = 10
    mock_config.INITIAL_RENT_PRICE = 100
    mock_config.INITIAL_WAGE = 10
    mock_config.EMERGENCY_STOCK_LIQUIDATION_FALLBACK_PRICE = 5
    mock_config.FALLBACK_SURVIVAL_COST = 5
    mock_config.DEFAULT_FOOD_PRICE_ESTIMATE = 5
    mock_config.HOUSEHOLD_MIN_WAGE_DEMAND = 5
    mock_config.SURVIVAL_BID_PREMIUM = 1
    mock_config.HOUSEHOLD_MIN_ASSETS_FOR_INVESTMENT = 10000
    mock_config.SURVIVAL_NEED_CONSUMPTION_THRESHOLD = 0.5
    mock_config.TARGET_FOOD_BUFFER_QUANTITY = 5.0
    mock_config.FOOD_PURCHASE_MAX_PER_TICK = 5.0
    mock_config.ASSETS_THRESHOLD_FOR_OTHER_ACTIONS = 100
    mock_config.WAGE_DECAY_RATE = 0.01
    mock_config.RESERVATION_WAGE_FLOOR = 1.0
    mock_config.MARKET_PRICE_FALLBACK = 5.0
    mock_config.NEED_FACTOR_BASE = 1.0
    mock_config.NEED_FACTOR_SCALE = 1.0
    mock_config.VALUATION_MODIFIER_BASE = 1.0
    mock_config.VALUATION_MODIFIER_RANGE = 0.1
    mock_config.HOUSEHOLD_MAX_PURCHASE_QUANTITY = 10.0
    mock_config.BULK_BUY_NEED_THRESHOLD = 0.8
    mock_config.BULK_BUY_AGG_THRESHOLD = 0.8
    mock_config.BULK_BUY_MODERATE_RATIO = 1.2
    mock_config.PANIC_BUYING_THRESHOLD = 0.2
    mock_config.HOARDING_FACTOR = 2.0
    mock_config.DEFLATION_WAIT_THRESHOLD = 0.05
    mock_config.DELAY_FACTOR = 0.5
    mock_config.DSR_CRITICAL_THRESHOLD = 0.4
    mock_config.BUDGET_LIMIT_NORMAL_RATIO = 0.8
    mock_config.BUDGET_LIMIT_URGENT_NEED = 0.9
    mock_config.BUDGET_LIMIT_URGENT_RATIO = 1.0
    mock_config.MIN_PURCHASE_QUANTITY = 0.1
    mock_config.JOB_QUIT_THRESHOLD_BASE = 0.3
    mock_config.JOB_QUIT_PROB_BASE = 0.1
    mock_config.JOB_QUIT_PROB_SCALE = 0.1
    mock_config.STOCK_MARKET_ENABLED = False
    mock_config.STOCK_INVESTMENT_EQUITY_DELTA_THRESHOLD = 0.1
    mock_config.STOCK_INVESTMENT_DIVERSIFICATION_COUNT = 5
    mock_config.EXPECTED_STARTUP_ROI = 0.1
    mock_config.DEBT_REPAYMENT_RATIO = 0.1
    mock_config.DEBT_REPAYMENT_CAP = 0.5
    mock_config.DEBT_LIQUIDITY_RATIO = 0.2
    mock_config.DEFAULT_MORTGAGE_RATE = 0.05
    mock_config.ENABLE_VANITY_SYSTEM = False
    mock_config.MIMICRY_FACTOR = 0.1
    mock_config.MAINTENANCE_RATE_PER_TICK = 0.001
    mock_config.HOUSING_EXPECTATION_CAP = 1.5
    mock_config.HOUSING_NPV_HORIZON_YEARS = 20
    mock_config.HOUSING_NPV_RISK_PREMIUM = 0.02
    mock_config.MORTGAGE_DEFAULT_DOWN_PAYMENT_RATE = 0.2
    mock_config.HOUSEHOLD_CONSUMABLE_GOODS = ['food']
    mock_config.WAGE_RECOVERY_RATE = 0.01
    mock_config.LEARNING_EFFICIENCY = 0.1
    mock_config.DEFAULT_FALLBACK_PRICE = 5
    mock_config.NEED_MEDIUM_THRESHOLD = 0.5
    mock_config.PANIC_SELLING_ASSET_THRESHOLD = 100
    mock_config.PERCEIVED_PRICE_UPDATE_FACTOR = 0.1
    mock_config.SOCIAL_STATUS_ASSET_WEIGHT = 0.5
    mock_config.SOCIAL_STATUS_LUXURY_WEIGHT = 0.5
    mock_config.BASE_DESIRE_GROWTH = 0.01
    mock_config.MAX_DESIRE_VALUE = 1.0
    mock_config.SURVIVAL_NEED_DEATH_THRESHOLD = 0.0
    mock_config.ASSETS_DEATH_THRESHOLD = 0
    mock_config.HOUSEHOLD_DEATH_TURNS_THRESHOLD = 100
    mock_config.SURVIVAL_NEED_DEATH_TICKS_THRESHOLD = 100
    mock_config.SURVIVAL_NEED_EMERGENCY_THRESHOLD = 0.2
    mock_config.PRIMARY_SURVIVAL_GOOD_ID = 'food'
    mock_config.MAX_WILLINGNESS_TO_PAY_MULTIPLIER = 2.0
    mock_config.EMERGENCY_LIQUIDATION_DISCOUNT = 0.5
    mock_config.DISTRESS_GRACE_PERIOD_TICKS = 10
    mock_config.AI_EPSILON_DECAY_PARAMS = (1.0, 0.01, 1000)
    mock_config.BASE_LABOR_SKILL = 1.0
    mock_config.SURVIVAL_BUDGET_ALLOCATION = 0.5
    mock_config.FOOD_CONSUMPTION_UTILITY = 1.0
    mock_config.SURVIVAL_CRITICAL_TURNS = 10
    mock_config.HOUSEHOLD_LOW_ASSET_THRESHOLD = 100
    mock_config.INSIGHT_DECAY_RATE = 0.01
    mock_config.INSIGHT_LEARNING_MULTIPLIER = 1.0
    mock_config.EDUCATION_BOOST_AMOUNT = 0.1
    mock_config.INSIGHT_THRESHOLD_REALTIME = 0.8
    mock_config.INSIGHT_THRESHOLD_SMA = 0.8
    mock_config.PANIC_TRIGGER_THRESHOLD = 0.2
    mock_config.DEBT_NOISE_FACTOR = 0.1
    mock_config.PANIC_CONSUMPTION_DAMPENER = 0.5
    mock_config.LABOR_MARKET = {}

    # 1. Setup Source Run
    run_id = in_memory_repo.runs.save_simulation_run("hash123", "Test Run", seed=42)

    # 2. Setup Agent Data (Household)
    # Construct complex state
    bio = BioStateDTO(id=101, age=25, gender="M", generation=1, is_active=True, needs={"survival": 0.5}, sex="M")

    wallet = Wallet(101, {"USD": 1000})
    portfolio = Portfolio(101)

    econ = EconStateDTO(
        wallet=wallet,
        inventory={"food": 10.0},
        inventory_quality={"food": 1.0},
        durable_assets=[],
        portfolio=portfolio,
        is_employed=True,
        employer_id=201,
        current_wage_pennies=5000,
        wage_modifier=1.0,
        labor_skill=1.2,
        education_xp=100.0,
        education_level=1,
        owned_properties=[],
        residing_property_id=None,
        is_homeless=False,
        home_quality_score=1.0,
        housing_target_mode="RENT",
        housing_price_history=deque([100, 102]),
        market_wage_history=deque([5000, 5100]),
        shadow_reservation_wage_pennies=4000,
        last_labor_offer_tick=0,
        last_fired_tick=-1,
        job_search_patience=10,
        employment_start_tick=0,
        current_consumption=10.0,
        current_food_consumption=5.0,
        expected_inflation={"CPI": 0.02},
        perceived_avg_prices={"food": 5.0},
        price_history=defaultdict(deque), # Simplified
        price_memory_length=10,
        adaptation_rate=0.1,
        labor_income_this_tick_pennies=0,
        capital_income_this_tick_pennies=0,
        consumption_expenditure_this_tick_pennies=0,
        food_expenditure_this_tick_pennies=0,
        talent=Talent(1.0, 1.0, 1.0)
    )

    social = SocialStateDTO(
        personality=Personality.GROWTH_ORIENTED,
        social_status=0.5,
        discontent=0.1,
        approval_rating=1,
        conformity=0.5,
        social_rank=0.5,
        quality_preference=0.8,
        brand_loyalty={},
        last_purchase_memory={},
        patience=0.5,
        optimism=0.6,
        ambition=0.7,
        last_leisure_type="IDLE"
    )

    hh_snapshot = HouseholdSnapshotDTO(id=101, bio_state=bio, econ_state=econ, social_state=social)
    hh_persistence = HouseholdPersistenceDTO(snapshot=hh_snapshot, distress_tick_counter=5)

    state_json = serialize_state(hh_persistence)

    hh_data = AgentStateData(
        run_id=run_id, time=100, agent_id=101, agent_type='household',
        assets={"USD": 1000}, is_active=True, generation=1,
        state_json=state_json
    )

    in_memory_repo.agents.save_agent_state(hh_data)

    # 3. Instantiate Initializer
    print(f"DEBUG: SimulationInitializer from {SimulationInitializer}")
    print(f"DEBUG: dir(SimulationInitializer): {dir(SimulationInitializer)}")

    initializer = SimulationInitializer(
        config_manager=config_manager,
        config_module=mock_config,
        goods_data=[],
        repository=in_memory_repo,
        logger=MagicMock(),
        households=[],
        firms=[],
        ai_trainer=MagicMock()
    )

    # Mock Phase 1-3 to return a dummy simulation
    # We patch _load_shocks if it exists, else we skip (to debug)
    # But batch_load_from_db CALLS it. So it must exist.

    with patch.object(initializer, '_init_phase1_infrastructure') as mock_p1, \
         patch.object(initializer, '_init_phase2_system_agents') as mock_p2, \
         patch.object(initializer, '_init_phase3_markets_systems') as mock_p3:

         # Mock _load_shocks via os.path.exists to prevent reading real file if method runs
         with patch('simulation.initialization.initializer.os.path.exists', return_value=False):

             sim = MagicMock()
             sim.agents = {}
             sim.households = []
             sim.firms = []
             sim.settlement_system = MagicMock()
             sim.bank = MagicMock()
             sim.bank.id = 999
             sim.agent_registry = MagicMock()
             sim.demographic_manager = MagicMock()
             sim.world_state = MagicMock()
             sim.persistence_manager = MagicMock()
             sim.crisis_monitor = MagicMock()
             sim.config = mock_config # Bind config

             mock_p1.return_value = sim

             # 4. Run Load
             restored_sim = initializer.batch_load_from_db(run_id)

         sim = MagicMock()
         sim.agents = {}
         sim.households = []
         sim.firms = []
         sim.settlement_system = MagicMock()
         sim.bank = MagicMock()
         sim.bank.id = 999
         sim.agent_registry = MagicMock()
         sim.demographic_manager = MagicMock()
         sim.world_state = MagicMock()
         sim.persistence_manager = MagicMock()
         sim.crisis_monitor = MagicMock()
         sim.config = mock_config # Bind config

         mock_p1.return_value = sim

         # 4. Run Load
         restored_sim = initializer.batch_load_from_db(run_id)

         # 5. Verify
         assert len(restored_sim.households) == 1
         agent = restored_sim.households[0]
         assert agent.id == 101
         assert agent.distress_tick_counter == 5
         assert agent._bio_state.age == 25
         assert agent._social_state.personality == Personality.GROWTH_ORIENTED
         assert restored_sim.time == 100
         assert restored_sim.run_id != run_id # New run ID

def test_load_shocks_deep_merge(in_memory_repo, config_manager, mock_config):
    """
    Verifies that _load_shocks correctly deep merges dicts into ScenarioStrategy.
    """
    from simulation.initialization.initializer import SimulationInitializer
    from simulation.dtos.strategy import ScenarioStrategy
    from unittest.mock import MagicMock, patch
    import json
    import os

    initializer = SimulationInitializer(
        config_manager=config_manager,
        config_module=mock_config,
        goods_data=[],
        repository=in_memory_repo,
        logger=MagicMock(),
        households=[],
        firms=[],
        ai_trainer=MagicMock()
    )

    strategy = ScenarioStrategy()
    strategy.exogenous_productivity_shock = {"FOOD": 1.0, "ENERGY": 1.0}
    strategy.parameters = {"param1": "A"}

    # Mock shocks.json content
    shocks_content = {
        "exogenous_productivity_shock": {"ENERGY": 0.5}, # Should update ENERGY, keep FOOD
        "parameters": {"param2": "B"} # Should update parameters (overwrite or merge? deep_merge merges)
    }

    with patch('simulation.initialization.initializer.os.path.exists', return_value=True), \
         patch('simulation.initialization.initializer.open', new_callable=MagicMock) as mock_open:

        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        # Mock json.load
        with patch('json.load', return_value=shocks_content):
             initializer._load_shocks(strategy)

    # Verify Deep Merge
    assert strategy.exogenous_productivity_shock["FOOD"] == 1.0
    assert strategy.exogenous_productivity_shock["ENERGY"] == 0.5
    assert strategy.parameters["param1"] == "A"
    assert strategy.parameters["param2"] == "B"

def test_seed_consistency(in_memory_repo, mock_config, config_manager):
    """
    Verifies that batch_load_from_db correctly restores RNG state,
    ensuring that subsequent random calls are deterministic.
    """
    from simulation.initialization.initializer import SimulationInitializer
    from simulation.dtos.strategy import ScenarioStrategy
    import random
    import numpy as np

    # 1. Setup Source Run with a seed
    seed = 12345
    run_id = in_memory_repo.runs.save_simulation_run("hash123", "Seed Test", seed=seed)

    # Mock repository responses since we are testing seed restoration logic, not data loading
    # We patch the methods on the instance retrieved from the fixture if needed,
    # but since it's an in-memory repo, we can just let it return empty data.
    # Actually, let's just use the repo as is; it returns empty lists if no data, which is fine.

    initializer = SimulationInitializer(
        config_manager=config_manager,
        config_module=mock_config,
        goods_data=[],
        repository=in_memory_repo,
        logger=MagicMock(),
        households=[],
        firms=[],
        ai_trainer=MagicMock()
    )

    # Mock initialization phases to do nothing
    with patch.object(initializer, '_init_phase1_infrastructure') as mock_p1, \
         patch.object(initializer, '_init_phase2_system_agents') as mock_p2, \
         patch.object(initializer, '_init_phase3_markets_systems') as mock_p3, \
         patch('simulation.initialization.initializer.os.path.exists', return_value=False):

         sim_mock = MagicMock()
         sim_mock.strategy = ScenarioStrategy()
         sim_mock.agents = {} # Required for loop
         sim_mock.households = []
         sim_mock.firms = []
         sim_mock.settlement_system = MagicMock()
         sim_mock.bank = MagicMock()
         sim_mock.agent_registry = MagicMock()
         sim_mock.demographic_manager = MagicMock()

         mock_p1.return_value = sim_mock

         # 2. Run Restoration
         initializer.batch_load_from_db(run_id)

         # 3. Check Determinism
         # Since batch_load_from_db calls random.seed(seed), the NEXT call to random() should be predictable.
         val1_random = random.random()
         val1_numpy = np.random.rand()

         # Reset manually to same seed to verify what we expect
         random.seed(seed)
         np.random.seed(seed)
         expected_random = random.random()
         expected_numpy = np.random.rand()

         assert val1_random == expected_random
         assert val1_numpy == expected_numpy
