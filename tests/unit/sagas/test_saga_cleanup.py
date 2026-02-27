import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
import logging

from modules.finance.sagas.orchestrator import SagaOrchestrator
from modules.finance.sagas.housing_api import HousingTransactionSagaStateDTO, HousingSagaAgentContext
from modules.simulation.api import HouseholdSnapshotDTO
from modules.system.api import IAgentRegistry

@pytest.fixture
def mock_registry():
    registry = MagicMock(spec=IAgentRegistry)
    # Default to active
    registry.is_agent_active.return_value = True
    return registry

@pytest.fixture
def saga_orchestrator(mock_registry):
    # Pass registry to constructor (Refactoring step)
    return SagaOrchestrator(agent_registry=mock_registry)

def test_saga_cleanup_inactive_buyer(saga_orchestrator, mock_registry, caplog):
    """
    Chaos Test: Manually set an agent to INACTIVE while it has a pending saga.
    Verifies that the saga is removed and cleaned up.
    """
    saga_id = uuid4()
    buyer_id = 101
    seller_id = 202

    saga = HousingTransactionSagaStateDTO(
        saga_id=saga_id,
        status="PENDING_OFFER",
        buyer_context=HouseholdSnapshotDTO(
            household_id=str(buyer_id), cash=1000, income=100,
            credit_score=700, existing_debt=0, assets_value=0
        ),
        seller_context=HousingSagaAgentContext(id=seller_id, monthly_income=500, existing_monthly_debt=0),
        property_id=500,
        offer_price=100,
        down_payment_amount=20,
        logs=[]
    )

    saga_orchestrator.submit_saga(saga)

    # Setup dependencies to avoid "Dependencies not fully injected" error
    saga_orchestrator.set_dependencies(
        settlement_system=MagicMock(),
        housing_service=MagicMock(),
        loan_market=MagicMock(),
        bank=MagicMock(),
        government=MagicMock()
    )

    # Setup Simulation State (Still needed for handler initialization)
    sim_state = MagicMock()
    # Mocks for agents are needed if logic accesses them directly,
    # but we are testing that it uses registry for liveness.
    # However, existing logic might still access agents for other things.
    sim_state.agents = {
        buyer_id: MagicMock(),
        seller_id: MagicMock()
    }
    sim_state.government = MagicMock()
    sim_state.government.id = 0
    saga_orchestrator.simulation_state = sim_state

    # CHAOS: Set Buyer to Inactive in Registry
    def side_effect(aid):
        if aid == buyer_id:
            return False
        return True
    mock_registry.is_agent_active.side_effect = side_effect

    with patch("modules.finance.sagas.orchestrator.HousingTransactionSagaHandler") as MockHandler:
        handler_instance = MockHandler.return_value

        # Run process
        with caplog.at_level(logging.INFO):
            saga_orchestrator.process_sagas(current_tick=1)

        # VERIFICATION

        # 1. Saga removed from active list
        assert saga_id not in saga_orchestrator.active_sagas

        # 2. Cleanup Log
        # "Saga {saga_id} cancelled due to inactive participant."
        assert any("cancelled due to inactive participant" in record.message for record in caplog.records)

        # 3. Compensation attempted (status PENDING_OFFER allows compensation?)
        # Logic says: if status not in ["INITIATED", "STARTED", "PENDING_OFFER"]: compensate
        # So PENDING_OFFER might skip compensation depending on exact logic.
        # Let's change status to CREDIT_CHECK to ensure compensation is called.

def test_saga_cleanup_and_compensate(saga_orchestrator, mock_registry, caplog):
    saga_id = uuid4()
    buyer_id = 101
    seller_id = 202

    saga = HousingTransactionSagaStateDTO(
        saga_id=saga_id,
        status="CREDIT_CHECK", # Beyond discovery
        buyer_context=HouseholdSnapshotDTO(
            household_id=str(buyer_id), cash=1000, income=100,
            credit_score=700, existing_debt=0, assets_value=0
        ),
        seller_context=HousingSagaAgentContext(id=seller_id, monthly_income=500, existing_monthly_debt=0),
        property_id=500,
        offer_price=100,
        down_payment_amount=20,
        logs=[]
    )

    saga_orchestrator.submit_saga(saga)

    saga_orchestrator.set_dependencies(
        settlement_system=MagicMock(),
        housing_service=MagicMock(),
        loan_market=MagicMock(),
        bank=MagicMock(),
        government=MagicMock()
    )
    saga_orchestrator.set_dependencies(
        settlement_system=MagicMock(),
        housing_service=MagicMock(),
        loan_market=MagicMock(),
        bank=MagicMock(),
        government=MagicMock()
    )

    sim_state = MagicMock()
    sim_state.agents = {buyer_id: MagicMock(), seller_id: MagicMock()}
    sim_state.government = MagicMock()
    sim_state.government.id = 0
    saga_orchestrator.simulation_state = sim_state

    # CHAOS: Seller Inactive
    def side_effect(aid):
        if aid == seller_id:
            return False
        return True
    mock_registry.is_agent_active.side_effect = side_effect

    with patch("modules.finance.sagas.orchestrator.HousingTransactionSagaHandler") as MockHandler:
        handler_instance = MockHandler.return_value

        saga_orchestrator.process_sagas(current_tick=1)

        # Check compensation called
        handler_instance.compensate_step.assert_called_once()
        assert saga_id not in saga_orchestrator.active_sagas

def test_saga_compensate_failure_resilience(saga_orchestrator, mock_registry, caplog):
    """
    Verifies that if compensation fails, the orchestrator logs error and continues (removes saga).
    """
    saga_id = uuid4()
    buyer_id = 101
    seller_id = 202

    saga = HousingTransactionSagaStateDTO(
        saga_id=saga_id,
        status="CREDIT_CHECK",
        buyer_context=HouseholdSnapshotDTO(
            household_id=str(buyer_id), cash=1000, income=100,
            credit_score=700, existing_debt=0, assets_value=0
        ),
        seller_context=HousingSagaAgentContext(id=seller_id, monthly_income=500, existing_monthly_debt=0),
        property_id=500,
        offer_price=100,
        down_payment_amount=20,
        logs=[]
    )

    saga_orchestrator.submit_saga(saga)

    saga_orchestrator.set_dependencies(
        settlement_system=MagicMock(),
        housing_service=MagicMock(),
        loan_market=MagicMock(),
        bank=MagicMock(),
        government=MagicMock()
    )

    sim_state = MagicMock()
    sim_state.agents = {buyer_id: MagicMock(), seller_id: MagicMock()}
    sim_state.government = MagicMock()
    sim_state.government.id = 0
    saga_orchestrator.simulation_state = sim_state

    # CHAOS: Inactive
    mock_registry.is_agent_active.return_value = False

    with patch("modules.finance.sagas.orchestrator.HousingTransactionSagaHandler") as MockHandler:
        handler_instance = MockHandler.return_value
        # Simulate Exception during compensation
        handler_instance.compensate_step.side_effect = Exception("Critical Compensation Failure")

        with caplog.at_level(logging.ERROR):
            saga_orchestrator.process_sagas(current_tick=1)

        # 1. Log SAGA_COMPENSATE_FAIL
        assert any("SAGA_COMPENSATE_FAIL" in record.message for record in caplog.records)

        # 2. Saga still removed
        assert saga_id not in saga_orchestrator.active_sagas
