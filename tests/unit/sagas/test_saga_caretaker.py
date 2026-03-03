import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from modules.finance.saga.api import ISagaRepository, ISagaOrchestrator, ISagaCaretaker, OrphanedSagaDTO
from modules.finance.saga.caretaker import SagaCaretaker
from modules.finance.api import SagaStateDTO
from modules.system.api import IAgentRegistry, AgentID

@pytest.fixture
def mock_saga_repository():
    return MagicMock(spec=ISagaRepository)

@pytest.fixture
def mock_saga_orchestrator():
    return MagicMock(spec=ISagaOrchestrator)

@pytest.fixture
def mock_agent_registry():
    return MagicMock(spec=IAgentRegistry)

@pytest.fixture
def caretaker(mock_saga_repository, mock_saga_orchestrator, mock_agent_registry):
    return SagaCaretaker(mock_saga_repository, mock_saga_orchestrator, mock_agent_registry)

def test_happy_path_sweep(caretaker, mock_saga_repository, mock_saga_orchestrator, mock_agent_registry):
    """Test standard sweep with one dead participant"""

    # Arrange
    saga_id = uuid4()
    mock_saga_repository.get_all_active_sagas.return_value = [
        SagaStateDTO(
            saga_id=saga_id,
            state="PENDING_INSPECTION",
            participant_ids=[1, 2],
            payload={"buyer_id": 1, "seller_id": 2},
            created_at=0,
            updated_at=0
        )
    ]

    def is_agent_active(agent_id):
        if agent_id == 1:
            return True
        elif agent_id == 2:
            return False

    mock_agent_registry.is_agent_active.side_effect = is_agent_active

    # Act
    purged_sagas = caretaker.sweep_orphaned_sagas(current_tick=1)

    # Assert
    assert len(purged_sagas) == 1
    assert purged_sagas[0].saga_id == saga_id
    assert purged_sagas[0].dead_participant_ids == [2]

    mock_saga_orchestrator.compensate_and_fail_saga.assert_called_once_with(
        saga_id,
        "Participant(s) Dead: [2]",
        1
    )

def test_idempotency_ignores_already_failed_sagas(caretaker, mock_saga_repository, mock_saga_orchestrator, mock_agent_registry):
    """Ensure already FAILED/COMPENSATING sagas are bypassed by the caretaker."""

    saga_id_failed = uuid4()
    saga_id_compensating = uuid4()

    mock_saga_repository.get_all_active_sagas.return_value = [
        SagaStateDTO(
            saga_id=saga_id_failed,
            state="FAILED",
            participant_ids=[1, 2],
            payload={"buyer_id": 1, "seller_id": 2},
            created_at=0,
            updated_at=0
        ),
        SagaStateDTO(
            saga_id=saga_id_compensating,
            state="COMPENSATING",
            participant_ids=[3, 4],
            payload={"buyer_id": 3, "seller_id": 4},
            created_at=0,
            updated_at=0
        )
    ]

    purged_sagas = caretaker.sweep_orphaned_sagas(current_tick=1)

    assert len(purged_sagas) == 0
    mock_agent_registry.is_agent_active.assert_not_called()
    mock_saga_orchestrator.compensate_and_fail_saga.assert_not_called()

def test_error_isolation(caretaker, mock_saga_repository, mock_saga_orchestrator, mock_agent_registry):
    """Mock `compensate_and_fail_saga` to throw an exception. Verify caretaker sweeps next without crashing."""

    saga_id_error = uuid4()
    saga_id_success = uuid4()

    mock_saga_repository.get_all_active_sagas.return_value = [
        SagaStateDTO(
            saga_id=saga_id_error,
            state="PENDING",
            participant_ids=[1, 2],
            payload={"buyer_id": 1, "seller_id": 2},
            created_at=0,
            updated_at=0
        ),
        SagaStateDTO(
            saga_id=saga_id_success,
            state="PENDING",
            participant_ids=[3, 4],
            payload={"buyer_id": 3, "seller_id": 4},
            created_at=0,
            updated_at=0
        )
    ]

    # All are dead
    mock_agent_registry.is_agent_active.return_value = False

    # First fails, second succeeds
    mock_saga_orchestrator.compensate_and_fail_saga.side_effect = [
        Exception("Failed to release lock!"),
        None
    ]

    purged_sagas = caretaker.sweep_orphaned_sagas(current_tick=1)

    # Second saga was swept successfully
    assert len(purged_sagas) == 1
    assert purged_sagas[0].saga_id == saga_id_success

    # Assert both were called
    assert mock_saga_orchestrator.compensate_and_fail_saga.call_count == 2
