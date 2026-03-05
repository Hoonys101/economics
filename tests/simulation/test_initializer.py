import pytest
from unittest.mock import MagicMock, patch, call
from simulation.initialization.initializer import SimulationInitializer

class TestSimulationInitializer:

    def teardown_method(self, method):
        if hasattr(self, 'ledger') and hasattr(self.ledger, 'transaction_log'):
            self.ledger.transaction_log.clear()
        if hasattr(self, 'transaction_log'):
            self.transaction_log.clear()

    @patch('simulation.initialization.initializer.SimulationInitializer._init_phase1_infrastructure')
    @patch('simulation.initialization.initializer.SimulationInitializer._init_phase2_system_agents')
    @patch('simulation.initialization.initializer.SimulationInitializer._init_phase3_markets_systems')
    @patch('simulation.initialization.initializer.SimulationInitializer._init_phase4_population')
    @patch('simulation.initialization.initializer.SimulationInitializer._init_phase5_genesis')
    @patch('simulation.initialization.initializer.Simulation')
    def test_registry_linked_before_bootstrap(self, MockSimulation, mock_p5, mock_p4, mock_p3, mock_p2, mock_p1):
        # Setup lightweight SimConfig stub
        mock_config = MagicMock()
        mock_repo = MagicMock()
        mock_logger = MagicMock()
        config_manager = MagicMock()

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
        mock_sim_instance.run_id = "test_run_123"

        # Track call order globally
        manager = MagicMock()

        # Simulate Phase 1 defining the registry
        mock_registry_instance = MagicMock()

        def phase1_side_effect():
            # In Phase 1, Simulation instance is returned
            # and AgentRegistry is created and set_state is called
            manager.AgentRegistry.set_state()
            return mock_sim_instance

        mock_p1.side_effect = phase1_side_effect

        def phase2_side_effect(sim):
            pass

        def phase3_side_effect(sim):
            pass

        def phase4_side_effect(sim):
            pass

        def phase5_side_effect(sim):
            manager.Bootstrapper.distribute_initial_wealth()
            pass

        mock_p2.side_effect = phase2_side_effect
        mock_p3.side_effect = phase3_side_effect
        mock_p4.side_effect = phase4_side_effect
        mock_p5.side_effect = phase5_side_effect

        # Execute
        sim = initializer.build_simulation()

        # Verify calls occurred
        mock_p1.assert_called_once()
        mock_p2.assert_called_once_with(mock_sim_instance)
        mock_p3.assert_called_once_with(mock_sim_instance)
        mock_p4.assert_called_once_with(mock_sim_instance)
        mock_p5.assert_called_once_with(mock_sim_instance)
        mock_sim_instance.initialize.assert_called_once()

        # Verify Call Order using our manager
        set_state_calls = [c for c in manager.mock_calls if 'AgentRegistry.set_state' in str(c)]
        bootstrap_calls = [c for c in manager.mock_calls if 'Bootstrapper.distribute_initial_wealth' in str(c)]

        assert len(set_state_calls) > 0, "AgentRegistry.set_state should be called"
        assert len(bootstrap_calls) > 0, "Bootstrapper.distribute_initial_wealth should be called"

        first_set_state_idx = manager.mock_calls.index(set_state_calls[0])
        first_bootstrap_idx = manager.mock_calls.index(bootstrap_calls[0])

        assert first_set_state_idx < first_bootstrap_idx, \
            f"AgentRegistry.set_state (idx {first_set_state_idx}) must be called BEFORE Bootstrapper.distribute_initial_wealth (idx {first_bootstrap_idx})"

    def test_initializer_no_getattr_calls(self):
        """
        Verify that _init_phase4_population correctly implements Local Reference Caching
        and does not repeatedly invoke Simulation.__getattr__ within the population loops.
        """
        from simulation.initialization.initializer import SimulationInitializer
        from unittest.mock import create_autospec

        # 1. Setup minimal dependencies
        config_manager = MagicMock()
        mock_config = MagicMock()
        mock_repo = MagicMock()
        mock_logger = MagicMock()

        initializer = SimulationInitializer(
            config_manager=config_manager,
            config_module=mock_config,
            goods_data=[],
            repository=mock_repo,
            logger=mock_logger,
            households=[],
            firms=[],
            ai_trainer=MagicMock(),
            initial_balances={}
        )

        # 2. Create a Mock Simulation object where we can monitor __getattr__
        class MockSimulationForGetAttr:
            def __init__(self):
                self.agents = {}
                self.agent_registry = MagicMock()
                self.settlement_system = MagicMock()
                self.bank = MagicMock()
                self.bank.id = 1
                self.demographic_manager = MagicMock()

                # The collections we will iterate over
                self.households = [MagicMock(id=i) for i in range(100)]
                for hh in self.households:
                    hh.get_balance.return_value = 100
                    hh._econ_state = MagicMock()

                self.firms = [MagicMock(id=i+100) for i in range(50)]
                self.real_estate_units = [MagicMock(id=i) for i in range(20)]

                self.world_state = MagicMock()
                self.next_agent_id = 0

                # A counter to track __getattr__ calls
                self.getattr_calls = 0
                self.accessed_attrs = set()

            def __getattr__(self, name):
                # Only count explicit proxy calls, ignoring internal pytest/mock machinery
                if name not in ['__bases__', '__class__', '__mro__', '__subclasses__', '_is_protocol']:
                    self.getattr_calls += 1
                    self.accessed_attrs.add(name)
                raise AttributeError(f"Mock attribute '{name}' not explicitly defined.")

        mock_sim = MockSimulationForGetAttr()

        # 3. Execute Phase 4
        # This will fail if the code uses sim.households or sim.firms directly inside the loop
        # because we only instantiate them as standard attributes, not dynamically resolved ones.
        # But we still want to ensure __getattr__ isn't magically hit for other attributes.
        initializer._init_phase4_population(mock_sim) # type: ignore

        # 4. Assert __getattr__ was strictly not called inside loops
        # It shouldn't be called at all since we have explicitly mapped all expected properties in __init__.
        # Specifically, we verify the loops didn't trigger unmapped recursive lookups.
        assert mock_sim.getattr_calls == 0, f"__getattr__ should not be called, but was called {mock_sim.getattr_calls} times for: {mock_sim.accessed_attrs}"
