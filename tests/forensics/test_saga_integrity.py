import pytest
from uuid import uuid4
from modules.finance.sagas.orchestrator import SagaOrchestrator
from modules.finance.sagas.housing_api import HousingTransactionSagaStateDTO, HousingSagaAgentContext
from modules.simulation.api import HouseholdSnapshotDTO

def test_saga_orchestrator_rejects_incomplete_dto():
    """
    Regression Test for TD-FORENSIC-002.
    Verifies that the Orchestrator rejects Sagas with missing critical IDs.
    """
    orchestrator = SagaOrchestrator()
    
    # 1. Setup Dirty DTO (Seller ID is None)
    # Note: seller_context.id is expected to be an int
    dirty_context = HousingSagaAgentContext(id=None, monthly_income=5000.0, existing_monthly_debt=1000.0)
    
    # buyer_context expects HouseholdSnapshotDTO
    buyer_context = HouseholdSnapshotDTO(
        household_id="101",
        cash=1000.0,
        income=5000.0,
        credit_score=750.0,
        existing_debt=0.0,
        assets_value=100000.0
    )
    
    dirty_saga = HousingTransactionSagaStateDTO(
        saga_id=uuid4(), 
        buyer_context=buyer_context,
        seller_context=dirty_context, # INVALID (id is None)
        status="INITIATED",
        property_id=5,
        offer_price=250000.0,
        down_payment_amount=50000.0
    )
    
    # 2. Submit
    # Expectation: Should reject or return False
    success = orchestrator.submit_saga(dirty_saga)
    
    # 3. Assert
    assert not success, "Orchestrator MUST reject Saga with missing seller_id"
    assert len(orchestrator.active_sagas) == 0
