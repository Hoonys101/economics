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
