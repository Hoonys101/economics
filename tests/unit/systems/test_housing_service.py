import pytest
from unittest.mock import MagicMock
from modules.housing.service import HousingService
from simulation.models import Transaction
from simulation.core_agents import Household
from simulation.dtos.api import SimulationState

def test_housing_service_handle_housing_updates_mortgage():
    service = HousingService()

    # Setup
    buyer = MagicMock(spec=Household)
    buyer.id = 1
    buyer.owned_properties = []
    buyer.residing_property_id = None
    buyer.is_homeless = True

    seller = MagicMock()
    seller.id = 2
    seller.owned_properties = [101]

    unit = MagicMock()
    unit.id = 101
    unit.owner_id = 2
    unit.liens = []
    unit.mortgage_id = None

    real_estate_units = [unit]
    service.set_real_estate_units(real_estate_units)

    state = MagicMock(spec=SimulationState)
    state.real_estate_units = real_estate_units
    state.time = 0
    state.agents = {1: buyer, 2: seller}

    # Transaction with mortgage_id
    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="unit_101", price=1000.0, quantity=1.0,
        market_id="housing", transaction_type="housing", time=0
    )
    tx.metadata = {"mortgage_id": "loan_999"}

    # Execute
    service.process_transaction(tx, state)

    # Verify
    assert unit.owner_id == 1
    # Check liens for mortgage
    assert any(l['loan_id'] == "loan_999" and l['lien_type'] == "MORTGAGE" for l in unit.liens)
    buyer.add_property.assert_called_with(101)
    assert 101 not in seller.owned_properties

def test_housing_service_handle_housing_clears_mortgage_if_missing():
    service = HousingService()

    buyer = MagicMock(spec=Household)
    buyer.id = 1
    buyer.owned_properties = []
    buyer.residing_property_id = None

    seller = MagicMock()
    seller.id = 2
    seller.owned_properties = [101]

    unit = MagicMock()
    unit.id = 101
    unit.owner_id = 2
    # Pre-existing mortgage
    unit.liens = [{
        "loan_id": "old_loan",
        "lienholder_id": 99,
        "principal_remaining": 500,
        "lien_type": "MORTGAGE"
    }]

    real_estate_units = [unit]
    service.set_real_estate_units(real_estate_units)

    state = MagicMock(spec=SimulationState)
    state.real_estate_units = real_estate_units
    state.time = 0
    state.agents = {1: buyer, 2: seller}

    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="unit_101", price=1000.0, quantity=1.0,
        market_id="housing", transaction_type="housing", time=0
    )
    tx.metadata = {} # No mortgage_id

    service.process_transaction(tx, state)

    assert unit.owner_id == 1
    # Should have cleared mortgage
    assert not any(l['lien_type'] == "MORTGAGE" for l in unit.liens)
