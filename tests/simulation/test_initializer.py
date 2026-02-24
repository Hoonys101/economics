import pytest
from unittest.mock import MagicMock, patch, call
from contextlib import ExitStack
from simulation.initialization.initializer import SimulationInitializer
from modules.system.constants import ID_GOVERNMENT, ID_CENTRAL_BANK, ID_BANK, ID_ESCROW, ID_PUBLIC_MANAGER

class TestSimulationInitializer:

    @patch('simulation.initialization.initializer.PlatformLockManager')
    @patch('simulation.initialization.initializer.Simulation')
    @patch('simulation.initialization.initializer.SettlementSystem')
    @patch('simulation.initialization.initializer.Bootstrapper')
    @patch('simulation.initialization.initializer.AgentRegistry')
    def test_registry_linked_before_bootstrap(self, MockAgentRegistry, MockBootstrapper, MockSettlementSystem, MockSimulation, MockLockManager):
        # Setup
        mock_config = MagicMock()
        mock_config.INITIAL_MONEY_SUPPLY = 1000
        mock_config.INITIAL_BANK_ASSETS = 1000
        # WO-STABILIZE-POST-MERGE: Ensure initial_bank_assets retrieved from config manager is an int, not a Mock
        mock_config.get.return_value = 1000
        mock_config.NUM_HOUSING_UNITS = 10
        mock_config.GOODS = ['food']
        mock_config.INITIAL_PROPERTY_VALUE = 100
        mock_config.INITIAL_RENT_PRICE = 10

        mock_repo = MagicMock()
        mock_logger = MagicMock()

        config_manager = MagicMock()
        # WO-STABILIZE-POST-MERGE: Ensure config_manager.get returns an int for 'initial_bank_assets'
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
            initial_balances={1: 100} # Trigger bootstrap for agent 1
        )

        mock_sim_instance = MockSimulation.return_value
        # Ensure sim.agents is a dict so update/assignment works
        mock_sim_instance.agents = {1: MagicMock()}

        mock_registry_instance = MockAgentRegistry.return_value
        # IMPORTANT: Link the registry mock to the simulation mock so calls to sim.agent_registry are tracked on the same object
        mock_sim_instance.agent_registry = mock_registry_instance

        # Create a manager to track call order
        manager = MagicMock()
        manager.attach_mock(MockBootstrapper, 'Bootstrapper')
        manager.attach_mock(mock_registry_instance, 'AgentRegistry')

        # List of components to mock to prevent initialization errors
        # Note: Local imports in build_simulation cannot be patched via simulation.initialization.initializer
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
            # Patch global imports
            patches = {}
            for component in components_to_mock:
                patches[component] = stack.enter_context(patch(f'simulation.initialization.initializer.{component}'))

            # Configure System Agent IDs to be integers (fixes TypeError in Phase 4 max() check)
            patches['Bank'].return_value.id = ID_BANK
            patches['Bank'].return_value.get_balance.return_value = 1000
            patches['Government'].return_value.id = ID_GOVERNMENT
            patches['CentralBank'].return_value.id = ID_CENTRAL_BANK
            patches['EscrowAgent'].return_value.id = ID_ESCROW
            patches['PublicManager'].return_value.id = ID_PUBLIC_MANAGER

            # Patch local imports at their source
            stack.enter_context(patch('modules.system.services.command_service.CommandService'))
            stack.enter_context(patch('modules.system.telemetry.TelemetryCollector'))
            stack.enter_context(patch('simulation.dtos.strategy.ScenarioStrategy'))
            stack.enter_context(patch('modules.analysis.scenario_verifier.engine.ScenarioVerifier'))

            initializer.build_simulation()

        # Verify LockManager usage
        MockLockManager.assert_called_with('simulation.lock')
        MockLockManager.return_value.acquire.assert_called_once()

        # Verify Call Order
        # We need to check if 'set_state' was called on the instance returned by AgentRegistry()
        # Since we mocked AgentRegistry class, verify method calls on its return value.

        # Note: manager.mock_calls tracks calls to attached mocks.
        # Bootstrapper is attached as 'Bootstrapper'.
        # AgentRegistry instance is attached as 'AgentRegistry'.

        set_state_calls = [c for c in manager.mock_calls if 'AgentRegistry.set_state' in str(c)]
        bootstrap_calls = [c for c in manager.mock_calls if 'Bootstrapper.distribute_initial_wealth' in str(c)]

        assert len(set_state_calls) > 0, "AgentRegistry.set_state should be called"
        assert len(bootstrap_calls) > 0, "Bootstrapper.distribute_initial_wealth should be called"

        # Get the index of the first call of each
        first_set_state_idx = manager.mock_calls.index(set_state_calls[0])
        first_bootstrap_idx = manager.mock_calls.index(bootstrap_calls[0])

        assert first_set_state_idx < first_bootstrap_idx, \
            f"AgentRegistry.set_state (idx {first_set_state_idx}) must be called BEFORE Bootstrapper.distribute_initial_wealth (idx {first_bootstrap_idx})"
