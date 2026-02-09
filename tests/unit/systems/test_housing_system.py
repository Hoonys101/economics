import unittest
from unittest.mock import MagicMock, patch
import pytest

from simulation.systems.housing_system import HousingSystem
from simulation.agents.government import Government

class TestHousingSystemRefactor(unittest.TestCase):

    def setUp(self):
        self.config_mock = MagicMock()
        self.config_mock.MAINTENANCE_RATE_PER_TICK = 0.01
        self.config_mock.HOMELESS_PENALTY_PER_TICK = 1.0
        self.config_mock.MORTGAGE_LTV_RATIO = 0.8
        self.config_mock.MORTGAGE_TERM_TICKS = 300
        self.config_mock.MORTGAGE_INTEREST_RATE = 0.05

        self.housing_system = HousingSystem(self.config_mock)

        # Setup Simulation Mock
        self.simulation = MagicMock()
        self.simulation.time = 100
        self.simulation.settlement_system = MagicMock()
        self.simulation.bank = MagicMock()
        self.simulation.government = MagicMock(spec=Government) # Specifically mock Government spec
        self.simulation.government.id = "GOVERNMENT"

        # Setup Agents
        self.tenant = MagicMock()
        self.tenant.id = 1
        self.tenant.assets = 1000.0
        self.tenant.is_active = True

        self.owner = MagicMock()
        self.owner.id = 2
        self.owner.assets = 5000.0
        self.owner.is_active = True

        self.buyer = MagicMock()
        self.buyer.id = 3
        self.buyer.assets = 20000.0 # Enough for downpayment
        self.buyer.is_active = True
        self.buyer.owned_properties = []
        self.buyer.residing_property_id = None # Ensure explicit None

        self.seller = MagicMock()
        self.seller.id = 4
        self.seller.assets = 50000.0
        self.seller.is_active = True
        self.seller.owned_properties = [101]

        self.simulation.agents = MagicMock()
        self.simulation.agents.get.side_effect = lambda x: {
            1: self.tenant,
            2: self.owner,
            3: self.buyer,
            4: self.seller,
            "GOVERNMENT": self.simulation.government,
            -1: self.simulation.government # Mock -1 as Government
        }.get(x)

        # Setup Units
        self.unit = MagicMock()
        self.unit.id = 101
        self.unit.owner_id = 2
        self.unit.occupant_id = 1
        self.unit.estimated_value = 10000.0
        self.unit.rent_price = 500.0
        self.unit.mortgage_id = None

        self.simulation.real_estate_units = [self.unit]

        # Default SettlementSystem transfer success
        self.simulation.settlement_system.transfer.return_value = True

        # Default Bank behavior
        # WO-024: grant_loan returns (dto, transaction)
        self.simulation.bank.grant_loan.return_value = ({"loan_id": "loan_123"}, MagicMock(transaction_type="credit_creation", price=100.0))
        self.simulation.bank.withdraw_for_customer.return_value = True
        self.simulation.bank.terminate_loan.return_value = MagicMock(transaction_type="credit_destruction")
        self.simulation.bank.void_loan.return_value = MagicMock(transaction_type="credit_destruction")

    def test_process_housing_rent_collection_uses_transfer(self):
        """Test that rent collection uses SettlementSystem.transfer"""
        # Arrange
        self.unit.owner_id = 2
        self.unit.occupant_id = 1

        # Act
        self.housing_system.process_housing(self.simulation)

        # Assert
        # Verify transfer was called for rent
        self.simulation.settlement_system.transfer.assert_any_call(
            self.tenant, self.owner, 500.0, "rent_payment", tick=100, currency='USD'
        )

        # Verify NO direct asset modification
        self.tenant._sub_assets.assert_not_called()
        self.owner._add_assets.assert_not_called()

    def test_process_housing_maintenance_uses_transfer(self):
        """Test that maintenance cost uses SettlementSystem.transfer"""
        # Arrange
        cost = 10000.0 * 0.01 # 100.0

        # Act
        self.housing_system.process_housing(self.simulation)

        # Assert
        self.simulation.settlement_system.transfer.assert_any_call(
            self.owner, self.simulation.government, cost, "housing_maintenance", tick=100, currency='USD'
        )

        # Verify NO direct asset modification (fallback)
        self.owner._sub_assets.assert_not_called()

