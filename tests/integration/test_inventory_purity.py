import unittest
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.base_agent import BaseAgent
from modules.simulation.api import IInventoryHandler, HouseholdSnapshotDTO
from unittest.mock import MagicMock

class TestInventoryPurity(unittest.TestCase):
    def test_inventory_protocol_compliance(self):
        """Verify that core agents implement the IInventoryHandler protocol."""
        self.assertTrue(issubclass(Household, IInventoryHandler))
        self.assertTrue(issubclass(Firm, IInventoryHandler))
        self.assertTrue(issubclass(BaseAgent, IInventoryHandler))

    def test_direct_access_removed(self):
        """Verify that the deprecated .inventory property is removed from BaseAgent."""
        # Check that 'inventory' is not a property or attribute of the class
        self.assertFalse(hasattr(BaseAgent, 'inventory'), "BaseAgent should not have 'inventory' property")

    def test_snapshot_dto_immutability(self):
        """Verify that HouseholdSnapshotDTO is immutable."""
        dto = HouseholdSnapshotDTO(
            household_id="1", cash=100.0, income=10.0, credit_score=700.0,
            existing_debt=0.0, assets_value=100.0
        )
        with self.assertRaises(Exception):
            dto.cash = 200.0 # Should raise FrozenInstanceError or similar

if __name__ == '__main__':
    unittest.main()
