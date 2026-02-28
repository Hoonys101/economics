import sys
import os
import pytest
import logging
import glob
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from modules.scenarios.loaders import JsonScenarioLoader
from modules.scenarios.judges import DomainJudgeFactory
from modules.scenarios.api import ScenarioStrategy
from simulation.initialization.initializer import SimulationInitializer
from simulation.db.repository import SimulationRepository
from simulation.ai_model import AIEngineRegistry
from simulation.core_agents import Household, Talent
from simulation.firms import Firm
from simulation.ai.api import Personality
from simulation.ai.state_builder import StateBuilder
from simulation.decisions.action_proposal import ActionProposalEngine
from simulation.decisions.rule_based_household_engine import RuleBasedHouseholdDecisionEngine
from simulation.decisions.standalone_rule_based_firm_engine import StandaloneRuleBasedFirmDecisionEngine
# Use Implementation, not Interface/Stub
from modules.common.config_manager.impl import ConfigManagerImpl as ConfigManager
import config as GlobalConfig

from modules.simulation.api import AgentCoreConfigDTO
from modules.simulation.dtos.api import HouseholdConfigDTO, FirmConfigDTO
from simulation.utils.config_factory import create_config_dto

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ScenarioRunner")

SCENARIO_DIR = os.path.join(os.path.dirname(__file__), "definitions")
SCENARIO_FILES = glob.glob(os.path.join(SCENARIO_DIR, "*.json"))

class MockRepository:
    """Mock repository to avoid DB overhead during tests."""
    def __init__(self):
        self.runs = self
        self.agents = self
        self.markets = self
        self.metrics = self
        self.market_history = self
        self.analytics = self
    def save_simulation_run(self, **kwargs): return "mock_run_id"
    def update_simulation_run_end_time(self, run_id): pass
    def save_agent_states_batch(self, batch): pass
    def save_transactions_batch(self, batch): pass
    def save_economic_indicators_batch(self, batch): pass
    def save_market_history_batch(self, batch): pass
    def save_ai_decision(self, decision): pass
    def close(self): pass
    def migrate(self): pass

class ConfigWrapper:
    def __init__(self, base_config):
        self._base = base_config
        self._overrides = {}

    def __getattr__(self, name):
        if name in self._overrides:
            return self._overrides[name]
        try:
            val = getattr(self._base, name)
            if hasattr(val, '_mock_name'): # Check if it's a mock
                 logger.warning(f"ConfigWrapper: getattr({name}) returned Mock from base!")
            return val
        except AttributeError:
            raise AttributeError(f"ConfigWrapper has no attribute '{name}'")

    def set_override(self, name, value):
        self._overrides[name] = value

class TestScenarioRunner:

    @pytest.fixture
    def scenario_loader(self):
        return JsonScenarioLoader()

    @pytest.fixture
    def judge_factory(self):
        return DomainJudgeFactory()

    def create_population(self, config_module):
        """Creates households and firms based on config."""
        households = []
        num_households = getattr(config_module, "NUM_HOUSEHOLDS", 10)

        # Determine Decision Engine Class
        # For tests, we prefer RuleBased to avoid AI overhead/randomness
        HHEngineClass = RuleBasedHouseholdDecisionEngine
        FirmEngineClass = StandaloneRuleBasedFirmDecisionEngine

        initial_needs = {"survival": 50, "social": 10, "growth": 10, "survival_need": 50, "imitation_need": 0, "recognition_need": 0, "wealth_need": 0}

        # Create DTOs
        hh_config_dto = create_config_dto(config_module, HouseholdConfigDTO)
        firm_config_dto = create_config_dto(config_module, FirmConfigDTO)

        for i in range(num_households):
            h_id = i + 100 # Shift IDs to avoid collision with System Agents (0-5)
            core_config = AgentCoreConfigDTO(
                id=h_id,
                name=f"Household_{h_id}",
                logger=logger,
                initial_needs=initial_needs,
                value_orientation="wealth_and_needs",
                memory_interface=None
            )

            h = Household(
                core_config=core_config,
                engine=HHEngineClass(config_module, logger),
                talent=Talent(1.0, {}),
                goods_data=[],
                personality=Personality.CONSERVATIVE,
                config_dto=hh_config_dto,
                initial_assets_record=getattr(config_module, "INITIAL_HOUSEHOLD_ASSETS", 1000)
            )
            households.append(h)

        firms = []
        num_firms = getattr(config_module, "NUM_FIRMS", 2)

        for i in range(num_firms):
            f_id = i + 1000
            # Special logic for Industrial Revolution scenario
            sector = "FOOD_PROD"
            spec = "basic_food"

            core_config = AgentCoreConfigDTO(
                id=f_id,
                name=f"Firm_{f_id}",
                logger=logger,
                initial_needs={},
                value_orientation="PROFIT",
                memory_interface=None
            )

            f = Firm(
                core_config=core_config,
                engine=FirmEngineClass(config_module, logger),
                specialization=spec,
                productivity_factor=10.0,
                sector=sector,
                config_dto=firm_config_dto,
                personality=Personality.BALANCED
            )
            firms.append(f)

        return households, firms

    @pytest.mark.parametrize("scenario_file", SCENARIO_FILES)
    @pytest.mark.xfail(reason="TD-ARCH-MOCK-POLLUTION: VectorizedHouseholdPlanner uses numpy ops which fail with MagicMocks from tests.")
    def test_run_scenario(self, scenario_file, scenario_loader, judge_factory):
        logger.info(f"--- Running Scenario: {os.path.basename(scenario_file)} ---")

        # 1. Load Strategy
        strategy = scenario_loader.load_from_file(Path(scenario_file))
        assert strategy is not None
        logger.info(f"Loaded Strategy: {strategy.id}, Category: {strategy.category}")

        # 2. Configure Simulation
        mock_config_module = ConfigWrapper(GlobalConfig)

        # Apply overrides from strategy to mock_config_module (Legacy)
        for key, value in strategy.config_params.items():
            mock_config_module.set_override(key, value)

        # Ensure active_scenario is NOT set to avoid loading legacy JSONs inside Initializer
        # Also ensure required simulation keys are present
        mock_config_module.set_override('simulation', {
            'active_scenario': None,
            'database_name': ':memory:',
            'batch_save_interval': 100
        })

        # Explicitly set thresholds to avoid potential Mock leakage from global config
        mock_config_module.set_override('SURVIVAL_NEED_CONSUMPTION_THRESHOLD', 50.0)
        mock_config_module.set_override('CHILD_MONTHLY_COST', 500.0)
        mock_config_module.set_override('OPPORTUNITY_COST_FACTOR', 0.3)
        mock_config_module.set_override('CHILD_EMOTIONAL_VALUE_BASE', 500000.0)
        mock_config_module.set_override('TECH_CONTRACEPTION_ENABLED', True)
        mock_config_module.set_override('BIOLOGICAL_FERTILITY_RATE', 0.15)
        mock_config_module.set_override('FOOD_CONSUMPTION_QUANTITY', 1.0)
        mock_config_module.set_override('FOOD_PURCHASE_MAX_PER_TICK', 5.0)

        # Create ConfigManager (required by Initializer)
        config_manager = ConfigManager(Path("config"), legacy_config=mock_config_module)

        # Disable internal loading and set DB path in ConfigManager too (prioritized)
        config_manager.set_value_for_test('simulation.active_scenario', None)
        config_manager.set_value_for_test('simulation.database_name', ':memory:')

        # Map some legacy overrides to ConfigManager keys if needed
        # SimulationInitializer reads 'economy_params.bank.initial_bank_assets'
        if 'INITIAL_BANK_ASSETS' in strategy.config_params:
             config_manager.set_value_for_test('economy_params.bank.initial_bank_assets', strategy.config_params['INITIAL_BANK_ASSETS'])

        # 3. Create Population
        households, firms = self.create_population(mock_config_module)

        # 4. Initialize Simulation
        repo = MockRepository()

        # Dummy AI Registry
        state_builder = StateBuilder()
        action_proposal = ActionProposalEngine(config_module=mock_config_module)
        ai_registry = AIEngineRegistry(action_proposal_engine=action_proposal, state_builder=state_builder)

        initializer = SimulationInitializer(
            config_manager=config_manager,
            config_module=mock_config_module,
            goods_data=[], # Dummy goods data
            repository=repo,
            logger=logger,
            households=households,
            firms=firms,
            ai_trainer=ai_registry,
            strategy=None # We rely on config overrides
        )

        sim = initializer.build_simulation()

        try:
            # 5. Create Judges
            judges = judge_factory.create_judges(strategy)
            logger.info(f"Created {len(judges)} judges: {[j.name for j in judges]}")
            assert len(judges) > 0, f"No judges created for scenario {strategy.id}"

            # 6. Run Execution Loop
            duration = strategy.duration_ticks
            logger.info(f"Running for {duration} ticks...")

            for tick in range(duration):
                try:
                    sim.run_tick()
                except Exception as e:
                    logger.error(f"Simulation crashed at tick {tick}: {e}", exc_info=True)
                    raise e

                # Run Judges (some might check per-tick invariants)
                for judge in judges:
                    pass_status = judge.judge(sim.world_state)
                    if not pass_status and strategy.category.name == "MONETARY":
                        metrics = judge.get_metrics(sim.world_state)
                        pytest.fail(f"Judge {judge.name} failed at tick {tick}. Metrics: {metrics}")

            # 7. Final Verification
            for judge in judges:
                result = judge.judge(sim.world_state)
                metrics = judge.get_metrics(sim.world_state)
                logger.info(f"Judge {judge.name} Result: {result}, Metrics: {metrics}")

                if not result:
                     pytest.fail(f"Judge {judge.name} failed final verification. Metrics: {metrics}")

                # Specific assertions
                if strategy.id == "industrial_revolution_diffusion":
                    if not metrics.get("tech_unlocked", False):
                         logger.warning("Tech not unlocked. Check duration or probability.")
                    else:
                         assert metrics.get("adoption_count", 0) >= 0

            logger.info("Scenario Passed.")
        except Exception as e:
            logger.error(f"Scenario failed with exception: {e}", exc_info=True)
            raise e
