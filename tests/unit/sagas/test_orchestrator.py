import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from modules.finance.sagas.orchestrator import SagaOrchestrator
from modules.finance.sagas.housing_api import HousingTransactionSagaStateDTO, HousingSagaAgentContext
from modules.simulation.api import HouseholdSnapshotDTO

@pytest.fixture
def saga_orchestrator():
    return SagaOrchestrator()

def test_submit_saga(saga_orchestrator):
    saga_id = uuid4()
    # Use dataclass constructor
    saga = HousingTransactionSagaStateDTO(
        saga_id=saga_id,
        status="INITIATED", # Use a valid literal
        buyer_context=HouseholdSnapshotDTO(household_id="1", cash=0, income=0, credit_score=0, existing_debt=0, assets_value=0),
        seller_context=HousingSagaAgentContext(id=2, monthly_income=0, existing_monthly_debt=0),
        property_id=500,
        offer_price=100.0,
        down_payment_amount=20.0
    )
    result = saga_orchestrator.submit_saga(saga)
    assert result is True
    assert saga_id in saga_orchestrator.active_sagas
    assert saga_orchestrator.active_sagas[saga_id] == saga

def test_process_sagas_liveness_check(saga_orchestrator):
    saga_id = uuid4()
    buyer_id = 1
    seller_id = 2

    saga = HousingTransactionSagaStateDTO(
        saga_id=saga_id,
        status="INITIATED",
        buyer_context=HouseholdSnapshotDTO(household_id=str(buyer_id), cash=0, income=0, credit_score=0, existing_debt=0, assets_value=0),
        seller_context=HousingSagaAgentContext(id=seller_id, monthly_income=0, existing_monthly_debt=0),
        property_id=500,
        offer_price=100.0,
        down_payment_amount=20.0,
        logs=[]
    )

    saga_orchestrator.submit_saga(saga)

    # Mock Simulation State
    sim_state = MagicMock()
    buyer = MagicMock()
    buyer.is_active = False # Inactive Buyer
    seller = MagicMock()
    seller.is_active = True

    sim_state.agents = {
        buyer_id: buyer,
        seller_id: seller
    }
    # Ensure government logic doesn't crash
    sim_state.government = MagicMock()
    sim_state.government.id = 0

    with patch("modules.finance.sagas.orchestrator.HousingTransactionSagaHandler") as MockHandler:
        saga_orchestrator.simulation_state = sim_state
        saga_orchestrator.process_sagas()

        # Should be removed from active sagas
        assert saga_id not in saga_orchestrator.active_sagas

        # Check logs if possible, but saga object might be gone from orchestrator.
        # But we hold a ref to 'saga'. It is mutable (dataclass).
        # Orchestrator modifies it in place.
        assert saga.status == "CANCELLED"
        assert "Cancelled due to inactive participant." in saga.logs

def test_process_sagas_active_participants(saga_orchestrator):
    saga_id = uuid4()
    buyer_id = 3
    seller_id = 4

    saga = HousingTransactionSagaStateDTO(
        saga_id=saga_id,
        status="INITIATED",
        buyer_context=HouseholdSnapshotDTO(household_id=str(buyer_id), cash=0, income=0, credit_score=0, existing_debt=0, assets_value=0),
        seller_context=HousingSagaAgentContext(id=seller_id, monthly_income=0, existing_monthly_debt=0),
        property_id=500,
        offer_price=100.0,
        down_payment_amount=20.0,
        logs=[]
    )

    saga_orchestrator.submit_saga(saga)

    sim_state = MagicMock()
    buyer = MagicMock()
    buyer.is_active = True
    seller = MagicMock()
    seller.is_active = True

    sim_state.agents = {
        buyer_id: buyer,
        seller_id: seller
    }
    sim_state.government = MagicMock()
    sim_state.government.id = 0

    with patch("modules.finance.sagas.orchestrator.HousingTransactionSagaHandler") as MockHandler:
        handler_instance = MockHandler.return_value
        # Return updated saga
        updated_saga = HousingTransactionSagaStateDTO(
            saga_id=saga_id, status="CREDIT_CHECK",
            buyer_context=saga.buyer_context, seller_context=saga.seller_context,
            property_id=500, offer_price=100, down_payment_amount=20
        )
        handler_instance.execute_step.return_value = updated_saga

        saga_orchestrator.simulation_state = sim_state
        saga_orchestrator.process_sagas()

        assert saga_id in saga_orchestrator.active_sagas
        assert saga_orchestrator.active_sagas[saga_id].status == "CREDIT_CHECK"

def test_find_and_compensate_by_agent_success(saga_orchestrator):
    saga_id = uuid4()
    agent_id = 999
    other_id = 888

    saga = HousingTransactionSagaStateDTO(
        saga_id=saga_id,
        status="APPROVED", # Use something that triggers logic
        buyer_context=HouseholdSnapshotDTO(household_id=str(agent_id), cash=0, income=0, credit_score=0, existing_debt=0, assets_value=0),
        seller_context=HousingSagaAgentContext(id=other_id, monthly_income=0, existing_monthly_debt=0),
        property_id=500,
        offer_price=100.0,
        down_payment_amount=20.0,
        logs=[]
    )

    saga_orchestrator.submit_saga(saga)

    mock_handler = MagicMock()
    # Return rolled back state
    rolled_back_saga = HousingTransactionSagaStateDTO(
        saga_id=saga_id, status="FAILED_ROLLED_BACK",
        buyer_context=saga.buyer_context, seller_context=saga.seller_context,
        property_id=500, offer_price=100, down_payment_amount=20
    )
    mock_handler.compensate_step.return_value = rolled_back_saga

    saga_orchestrator.find_and_compensate_by_agent(agent_id, mock_handler)

    mock_handler.compensate_step.assert_called_with(saga)
    assert saga_id not in saga_orchestrator.active_sagas

def test_find_and_compensate_by_agent_no_handler(saga_orchestrator):
    saga_id = uuid4()
    agent_id = 777

    saga = HousingTransactionSagaStateDTO(
        saga_id=saga_id,
        status="INITIATED",
        buyer_context=HouseholdSnapshotDTO(household_id=str(agent_id), cash=0, income=0, credit_score=0, existing_debt=0, assets_value=0),
        seller_context=HousingSagaAgentContext(id=666, monthly_income=0, existing_monthly_debt=0),
        property_id=500,
        offer_price=100.0,
        down_payment_amount=20.0
    )
    saga_orchestrator.submit_saga(saga)

    saga_orchestrator.find_and_compensate_by_agent(agent_id, None)

    # Should handle error gracefully and not crash
    assert saga_id in saga_orchestrator.active_sagas
