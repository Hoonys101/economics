import pytest
from unittest.mock import MagicMock
from simulation.models import RealEstateUnit
from modules.finance.api import LienDTO, IRealEstateRegistry

def test_real_estate_unit_initialization():
    """Test standard initialization without optional deps."""
    unit = RealEstateUnit(id=1, estimated_value=50000)
    assert unit.id == 1
    assert unit.liens == []
    assert unit.mortgage_id is None
    assert unit.is_under_contract is False

def test_liens_management():
    """Test adding/removing liens."""
    unit = RealEstateUnit(id=2)

    lien1: LienDTO = {
        "loan_id": "loan_101",
        "lienholder_id": 99,
        "principal_remaining": 40000,
        "lien_type": "MORTGAGE"
    }

    unit.liens.append(lien1)

    assert len(unit.liens) == 1
    assert unit.mortgage_id == "loan_101"

    # Add another lien (tax)
    lien2: LienDTO = {
        "loan_id": "tax_2022",
        "lienholder_id": 0,
        "principal_remaining": 500,
        "lien_type": "TAX_LIEN"
    }
    unit.liens.append(lien2)

    assert len(unit.liens) == 2
    # mortgage_id should still find the mortgage
    assert unit.mortgage_id == "loan_101"

def test_is_under_contract_delegation():
    """Test delegation to registry."""
    unit = RealEstateUnit(id=3)

    # Mock Registry
    registry = MagicMock(spec=IRealEstateRegistry)
    registry.is_under_contract.return_value = True

    # Inject dependency
    unit._registry_dependency = registry

    assert unit.is_under_contract is True
    registry.is_under_contract.assert_called_with(3)

    registry.is_under_contract.return_value = False
    assert unit.is_under_contract is False

def test_mortgage_id_backward_compatibility():
    """Test read-only property logic."""
    unit = RealEstateUnit(id=4)
    assert unit.mortgage_id is None

    unit.liens.append({
        "loan_id": "loan_XYZ",
        "lienholder_id": 1,
        "principal_remaining": 100,
        "lien_type": "MORTGAGE"
    })

    assert unit.mortgage_id == "loan_XYZ"

    # Check that it ignores other types
    unit.liens = [{
        "loan_id": "tax_1",
        "lienholder_id": 0,
        "principal_remaining": 100,
        "lien_type": "TAX_LIEN"
    }]
    assert unit.mortgage_id is None
