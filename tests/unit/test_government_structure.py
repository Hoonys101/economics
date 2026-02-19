import pytest
from unittest.mock import MagicMock, patch
from simulation.world_state import WorldState
from simulation.agents.government import Government
from simulation.engine import Simulation
from modules.common.config_manager.api import ConfigManager

class TestGovernmentStructure:
    def test_government_property_proxy(self):
        """Verify that WorldState.government property proxies to governments[0]."""
        # Setup WorldState
        mock_config_manager = MagicMock(spec=ConfigManager)
        mock_logger = MagicMock()
        mock_repo = MagicMock()

        ws = WorldState(mock_config_manager, None, mock_logger, mock_repo)

        # Initially empty
        assert ws.government is None
        assert ws.governments == []

        # Create a mock Government
        mock_gov = MagicMock(spec=Government)
        mock_gov.id = 1

        # Append directly
        ws.governments.append(mock_gov)

        # Verify property access
        assert ws.government is mock_gov
        assert ws.government.id == 1

    def test_government_setter_sync(self):
        """Verify that setting WorldState.government updates governments list."""
        # Setup WorldState
        mock_config_manager = MagicMock(spec=ConfigManager)
        mock_logger = MagicMock()
        mock_repo = MagicMock()

        ws = WorldState(mock_config_manager, None, mock_logger, mock_repo)

        mock_gov1 = MagicMock(spec=Government)
        mock_gov1.id = 101

        # Set via property
        ws.government = mock_gov1

        assert len(ws.governments) == 1
        assert ws.governments[0] is mock_gov1
        assert ws.government is mock_gov1

        # Replace via property
        mock_gov2 = MagicMock(spec=Government)
        mock_gov2.id = 102

        ws.government = mock_gov2

        assert len(ws.governments) == 1
        assert ws.governments[0] is mock_gov2
        assert ws.government is mock_gov2

    def test_simulation_delegation(self):
        """Verify that Simulation delegates government access to WorldState."""
        # Mock dependencies for Simulation
        mock_config_manager = MagicMock(spec=ConfigManager)
        mock_config_manager.get.return_value = "simulation_test.db"
        mock_logger = MagicMock()
        mock_repo = MagicMock()
        mock_registry = MagicMock()
        mock_settlement = MagicMock()
        mock_agent_registry = MagicMock()
        mock_command_service = MagicMock()

        # We need to mock SimulationLogger to avoid creating a DB file
        with patch('simulation.engine.SimulationLogger'):
            sim = Simulation(
                mock_config_manager,
                None,
                mock_logger,
                mock_repo,
                mock_registry,
                mock_settlement,
                mock_agent_registry,
                mock_command_service
            )

        # Setup Mock Government
        mock_gov = MagicMock(spec=Government)

        # Set via Simulation (delegates to WorldState setter)
        sim.government = mock_gov

        assert sim.world_state.governments[0] is mock_gov
        assert sim.government is mock_gov

        # Verify list integrity
        assert len(sim.world_state.governments) == 1
