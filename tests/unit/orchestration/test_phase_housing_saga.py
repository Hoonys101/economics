import pytest
from unittest.mock import MagicMock
from simulation.orchestration.phases import Phase_HousingSaga
from simulation.dtos.api import SimulationState

def test_phase_housing_saga_execution():
    # Setup
    mock_world_state = MagicMock()
    phase = Phase_HousingSaga(mock_world_state)

    mock_state = MagicMock(spec=SimulationState)
    mock_state.time = 1
    mock_saga_orchestrator = MagicMock()
    mock_state.saga_orchestrator = mock_saga_orchestrator

    # Execute
    phase.execute(mock_state)

    # Verify
    mock_saga_orchestrator.process_sagas.assert_called_once_with(1)

def test_phase_housing_saga_execution_fallback():
    # Setup
    mock_world_state = MagicMock()
    phase = Phase_HousingSaga(mock_world_state)

    mock_state = MagicMock(spec=SimulationState)
    mock_state.time = 1
    mock_state.saga_orchestrator = None
    mock_settlement_system = MagicMock()
    mock_state.settlement_system = mock_settlement_system

    # Execute
    phase.execute(mock_state)

    # Verify
    mock_settlement_system.process_sagas.assert_called_once_with(mock_state)

def test_phase_housing_saga_no_settlement_system():
    # Setup
    mock_world_state = MagicMock()
    phase = Phase_HousingSaga(mock_world_state)

    mock_state = MagicMock(spec=SimulationState)
    mock_state.time = 1
    mock_state.settlement_system = None

    # Execute (should not raise error)
    result_state = phase.execute(mock_state)

    # Verify
    assert result_state == mock_state

def test_phase_housing_saga_system_no_method():
    # Setup
    mock_world_state = MagicMock()
    phase = Phase_HousingSaga(mock_world_state)

    mock_state = MagicMock(spec=SimulationState)
    mock_state.time = 1
    mock_settlement_system = MagicMock()
    # Ensure hasattr(..., 'process_sagas') returns False
    # MagicMock usually creates attributes on access, so we need to be careful.
    # We can use a spec that does not have process_sagas, or just a plain object.

    class MockSystemWithoutMethod:
        pass

    mock_state.settlement_system = MockSystemWithoutMethod()

    # Execute (should not raise error)
    phase.execute(mock_state)
