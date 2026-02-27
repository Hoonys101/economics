import pytest
from unittest.mock import MagicMock, patch, call
from contextlib import ExitStack
from simulation.initialization.initializer import SimulationInitializer
from modules.system.constants import ID_GOVERNMENT, ID_CENTRAL_BANK, ID_BANK, ID_ESCROW, ID_PUBLIC_MANAGER

class TestAtomicStartup:

    @pytest.mark.no_lock_mock
    @patch.dict('os.environ', {"FORCE_SIM_LOCK_TEST": "1"})
    @patch('simulation.initialization.initializer.PlatformLockManager', autospec=True)
    @patch('simulation.initialization.initializer.Simulation', autospec=True)
    @patch('simulation.initialization.initializer.SettlementSystem', autospec=True)
    @patch('simulation.initialization.initializer.Bootstrapper', autospec=True)
    @patch('simulation.initialization.initializer.AgentRegistry', autospec=True)
    def test_atomic_startup_phase_validation(self, MockAgentRegistry, MockBootstrapper, MockSettlementSystem, MockSimulation, MockLockManager):
        """
        Verifies that the 5-phase initialization sequence executes without error
        and maintains critical dependency ordering.
        """
        # Setup
        mock_config = MagicMock()
        mock_config.INITIAL_MONEY_SUPPLY = 1000
        mock_config.INITIAL_BANK_ASSETS = 1000
        mock_config.get.return_value = 1000
        mock_config.NUM_HOUSING_UNITS = 10
        mock_config.GOODS = ['food']
        mock_config.INITIAL_PROPERTY_VALUE = 100
        mock_config.INITIAL_RENT_PRICE = 10

        mock_repo = MagicMock()
        mock_logger = MagicMock()

        config_manager = MagicMock()
        config_manager.get.return_value = 1000

        initializer = SimulationInitializer(
            config_manager=config_manager,
            config_module=mock_config,
            goods_data=[],
            repository=mock_repo,
            logger=mock_logger,
            households=[],
            firms=[],
            ai_trainer=MagicMock(),
            initial_balances={1: 100}
        )

        mock_sim_instance = MockSimulation.return_value
        mock_sim_instance.agents = {1: MagicMock()}
        mock_sim_instance.world_state = MagicMock()
        mock_sim_instance.world_state.global_registry = MagicMock()
        mock_sim_instance.world_state.transactions = MagicMock()
        mock_sim_instance.settlement_system = MockSettlementSystem.return_value
        mock_sim_instance.government = MagicMock() # Required to pass hasattr check in Phase 2
        mock_sim_instance.firms = [] # Required for Phase 3 if Stock Market enabled
        mock_sim_instance.households = []
        mock_sim_instance.run_id = "test_run_id" # Required for Phase 3
        mock_registry_instance = MockAgentRegistry.return_value
        mock_sim_instance.agent_registry = mock_registry_instance

        # Track calls
        manager = MagicMock()
        manager.attach_mock(MockBootstrapper, 'Bootstrapper')
        manager.attach_mock(mock_registry_instance, 'AgentRegistry')
        manager.attach_mock(MockLockManager, 'LockManager')
        manager.attach_mock(MockSettlementSystem, 'SettlementSystem')

        # Mock ALL the things to avoid import errors and side effects
        components_to_mock = [
            'GlobalRegistry', 'EventBus', 'TaxationSystem',
            'MonetaryLedger', 'SagaOrchestrator', 'ShareholderRegistry', 'EconomicIndicatorTracker',
            'CentralBank', 'Bank', 'Government', 'FinanceSystem', 'RealEstateUnit',
            'OrderBookMarket', 'LaborMarket', 'LoanMarket', 'InequalityTracker', 'PersonalityStatisticsTracker',
            'AITrainingManager', 'MAManager', 'PersistenceManager', 'HouseholdFactory', 'DemographicManager',
            'ImmigrationManager', 'InheritanceManager', 'HousingSystem', 'AnalyticsSystem', 'FirmSystem',
            'TechnologyManager', 'GenerationalWealthAudit', 'VectorizedHouseholdPlanner', 'TransactionProcessor',
            'AgentLifecycleManager', 'SocialSystem', 'EventSystem', 'SensorySystem', 'CommerceSystem',
            'LaborMarketAnalyzer', 'CrisisMonitor', 'EscrowAgent', 'JudicialSystem',
            'PublicManager', 'HousingService', 'Registry', 'AccountingSystem', 'CentralBankSystem',
            'CreditScoringService'
        ]

        with ExitStack() as stack:
            patches = {}
            for component in components_to_mock:
                patches[component] = stack.enter_context(patch(f'simulation.initialization.initializer.{component}', autospec=True))

            # Configure System Agent IDs to be integers (fixes TypeError in Phase 4 max() check)
            patches['Bank'].return_value.id = ID_BANK
            patches['Bank'].return_value.base_rate = 0.05 # Phase 5 access
            patches['Bank'].return_value.get_balance.return_value = 1000
            patches['Government'].return_value.id = ID_GOVERNMENT
            patches['CentralBank'].return_value.id = ID_CENTRAL_BANK
            patches['EscrowAgent'].return_value.id = ID_ESCROW
            patches['PublicManager'].return_value.id = ID_PUBLIC_MANAGER

            patches['HouseholdFactory'].return_value.context = MagicMock()

            stack.enter_context(patch('modules.system.services.command_service.CommandService', autospec=True))
            stack.enter_context(patch('modules.system.telemetry.TelemetryCollector', autospec=True))
            stack.enter_context(patch('simulation.dtos.strategy.ScenarioStrategy', autospec=True))
            stack.enter_context(patch('modules.analysis.scenario_verifier.engine.ScenarioVerifier', autospec=True))

            # Execute
            sim = initializer.build_simulation()

        # Assertions for Phase Sequence (Logical Check)

        # Phase 1: Lock -> Registry
        assert MockLockManager.return_value.acquire.called, "Phase 1: Lock must be acquired"

        # Phase 2: System Agents (Bank, Gov)
        # We can't easily check Bank instantiation without mocking it and attaching to manager,
        # but we can check if they are in sim.agents or similar if we inspected sim.

        # Phase 5: Bootstrap
        assert MockBootstrapper.distribute_initial_wealth.called, "Phase 5: Bootstrapper must be called"

        # Check Order: Lock -> Registry -> Bootstrap
        calls = manager.mock_calls
        lock_calls = [c for c in calls if 'LockManager' in str(c)] # Acquire
        registry_calls = [c for c in calls if 'AgentRegistry.set_state' in str(c)]
        bootstrap_calls = [c for c in calls if 'Bootstrapper.distribute_initial_wealth' in str(c)]

        assert len(lock_calls) > 0, "LockManager should be called"
        assert len(registry_calls) > 0, "AgentRegistry.set_state should be called"
        assert len(bootstrap_calls) > 0, "Bootstrapper should be called"

        first_lock = calls.index(lock_calls[0])
        first_registry = calls.index(registry_calls[0])
        first_bootstrap = calls.index(bootstrap_calls[0])

        assert first_lock < first_registry, "Phase 1 (Lock) must happen before Phase 2 (Registry Link)"
        assert first_registry < first_bootstrap, "Phase 2 (Registry Link) must happen before Phase 5 (Genesis)"

        # Check return
        assert sim == mock_sim_instance
