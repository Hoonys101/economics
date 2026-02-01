import pytest
from unittest.mock import MagicMock
from simulation.systems.registry import Registry
from simulation.models import Transaction
from simulation.core_agents import Household
from simulation.dtos.api import SimulationState

def test_registry_handle_housing_updates_mortgage():
    registry = Registry()

    # Setup
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
    unit.mortgage_id = None

    real_estate_units = [unit]

    state = MagicMock(spec=SimulationState)
    state.real_estate_units = real_estate_units
    state.time = 0

    # Transaction with mortgage_id
    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="unit_101", price=1000.0, quantity=1.0,
        market_id="housing", transaction_type="housing", time=0
    )
    tx.metadata = {"mortgage_id": "loan_999"}

    # Execute
    registry.update_ownership(tx, buyer, seller, state)

    # Verify
    assert unit.owner_id == 1
    assert unit.mortgage_id == "loan_999"
    assert 101 in buyer.owned_properties
    assert 101 not in seller.owned_properties

def test_registry_handle_housing_clears_mortgage_if_missing():
    registry = Registry()

    buyer = MagicMock(spec=Household)
    buyer.id = 1
    buyer.owned_properties = []

    seller = MagicMock()
    seller.id = 2
    seller.owned_properties = [101]

    unit = MagicMock()
    unit.id = 101
    unit.owner_id = 2
    unit.mortgage_id = "old_loan"

    real_estate_units = [unit]
    state = MagicMock(spec=SimulationState)
    state.real_estate_units = real_estate_units
    state.time = 0

    tx = Transaction(
        buyer_id=1, seller_id=2, item_id="unit_101", price=1000.0, quantity=1.0,
        market_id="housing", transaction_type="housing", time=0
    )
    tx.metadata = {} # No mortgage_id

    registry.update_ownership(tx, buyer, seller, state)

    assert unit.owner_id == 1
    assert unit.mortgage_id is None
