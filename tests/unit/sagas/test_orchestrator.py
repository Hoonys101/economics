import pytest
from unittest.mock import MagicMock, patch
from modules.finance.sagas.orchestrator import SagaOrchestrator
from modules.finance.sagas.housing_api import HousingTransactionSagaStateDTO

@pytest.fixture
def saga_orchestrator():
    return SagaOrchestrator()

def test_submit_saga(saga_orchestrator):
    saga_id = "test-saga-uuid"
    saga = {
        "saga_id": saga_id,
        "status": "STARTED"
    }
    result = saga_orchestrator.submit_saga(saga)
    assert result is True
    assert saga_id in saga_orchestrator.active_sagas

def test_process_sagas_liveness_check(saga_orchestrator):
    saga_id = "test-saga-uuid"
    buyer_id = 1
    seller_id = 2

    saga = {
        "saga_id": saga_id,
        "buyer_id": buyer_id,
        "seller_id": seller_id,
        "status": "STARTED",
        "logs": []
    }

    saga_orchestrator.submit_saga(saga)

    mock_state = MagicMock()
    mock_state.agents = {}

    mock_buyer = MagicMock()
    mock_buyer.is_active = False
    mock_seller = MagicMock()
    mock_seller.is_active = True

    mock_state.agents[buyer_id] = mock_buyer
    mock_state.agents[seller_id] = mock_seller

    with patch("modules.finance.sagas.orchestrator.HousingTransactionSagaHandler") as MockHandler:
        mock_handler_instance = MockHandler.return_value
        mock_handler_instance.execute_step.return_value = saga

        saga_orchestrator.process_sagas(mock_state)

        assert saga_id not in saga_orchestrator.active_sagas
        assert saga["status"] == "CANCELLED"
        # execute_step should not be called if cancelled
        mock_handler_instance.execute_step.assert_not_called()
        # compensate should be called
        mock_handler_instance.compensate_step.assert_called_once()

def test_process_sagas_active_participants(saga_orchestrator):
    saga_id = "test-saga-uuid-2"
    buyer_id = 3
    seller_id = 4

    saga = {
        "saga_id": saga_id,
        "buyer_id": buyer_id,
        "seller_id": seller_id,
        "status": "STARTED",
        "logs": []
    }

    saga_orchestrator.submit_saga(saga)

    mock_state = MagicMock()
    mock_state.agents = {}

    mock_buyer = MagicMock()
    mock_buyer.is_active = True
    mock_seller = MagicMock()
    mock_seller.is_active = True

    mock_state.agents[buyer_id] = mock_buyer
    mock_state.agents[seller_id] = mock_seller

    with patch("modules.finance.sagas.orchestrator.HousingTransactionSagaHandler") as MockHandler:
        mock_handler_instance = MockHandler.return_value
        updated_saga = saga.copy()
        updated_saga["status"] = "PENDING_OFFER"
        mock_handler_instance.execute_step.return_value = updated_saga

        saga_orchestrator.process_sagas(mock_state)

        assert saga_id in saga_orchestrator.active_sagas
        assert saga_orchestrator.active_sagas[saga_id]["status"] == "PENDING_OFFER"
        mock_handler_instance.execute_step.assert_called_once_with(saga)

def test_find_and_compensate_by_agent_success(saga_orchestrator):
    saga_id = "saga-compensation-test"
    agent_id = 999
    other_id = 888

    saga = {
        "saga_id": saga_id,
        "buyer_id": agent_id,
        "seller_id": other_id,
        "status": "PENDING_OFFER",
        "logs": []
    }

    saga_orchestrator.submit_saga(saga)

    # Mock Handler
    mock_handler = MagicMock()
    # Compensate returns updated saga
    compensated_saga = saga.copy()
    compensated_saga["status"] = "FAILED_ROLLED_BACK"
    mock_handler.compensate_step.return_value = compensated_saga

    saga_orchestrator.find_and_compensate_by_agent(agent_id, handler=mock_handler)

    # Should be removed if status becomes FAILED_ROLLED_BACK
    assert saga_id not in saga_orchestrator.active_sagas
    mock_handler.compensate_step.assert_called_once()

def test_find_and_compensate_by_agent_no_handler(saga_orchestrator):
    saga_id = "saga-no-handler"
    agent_id = 777

    saga = {
        "saga_id": saga_id,
        "buyer_id": agent_id,
        "seller_id": 666,
        "status": "STARTED"
    }
    saga_orchestrator.submit_saga(saga)

    # Call without handler
    saga_orchestrator.find_and_compensate_by_agent(agent_id, handler=None)

    # Saga should remain untouched (logged error)
    assert saga_id in saga_orchestrator.active_sagas
