import unittest
from unittest.mock import MagicMock, patch
import pytest

from simulation.systems.housing_system import HousingSystem
from simulation.models import Transaction, Order
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
            self.tenant, self.owner, 500.0, "rent_payment", tick=100
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
            self.owner, self.simulation.government, cost, "housing_maintenance", tick=100
        )

        # Verify NO direct asset modification (fallback)
        self.owner._sub_assets.assert_not_called()

    def test_process_transaction_uses_transfer_and_withdraw(self):
        """Test the full transaction flow: Loan -> Transfer(Bank->Buyer) -> Withdraw(Liability) -> Transfer(Buyer->Seller)"""
        # Arrange
        tx = Transaction(
            buyer_id=3,
            seller_id=4,
            item_id="unit_101",
            price=10000.0,
            quantity=1.0,
            market_id="housing",
            transaction_type="purchase",
            time=100
        )

        # Config
        self.config_mock.MORTGAGE_LTV_RATIO = 0.8
        loan_amount = 8000.0
        trade_value = 10000.0

        # Act
        self.housing_system.process_transaction(tx, self.simulation)

        # Assert

        # 1. Loan Disbursement: Bank -> Buyer (Asset Transfer)
        self.simulation.settlement_system.transfer.assert_any_call(
            self.simulation.bank, self.buyer, loan_amount, "loan_disbursement", tick=100
        )

        # 2. Deposit Cleanup: Bank.withdraw_for_customer (Liability Reduction)
        self.simulation.bank.withdraw_for_customer.assert_called_with(3, loan_amount)

        # 3. Payment: Buyer -> Seller
        self.simulation.settlement_system.transfer.assert_any_call(
            self.buyer, self.seller, trade_value, "purchase_unit_101", tick=100
        )

        # 4. Ownership Transfer
        self.assertEqual(self.unit.owner_id, 3)
        self.assertEqual(self.unit.occupant_id, 3)

        # 5. NO direct asset modification
        self.buyer._add_assets.assert_not_called()
        self.buyer._sub_assets.assert_not_called()
        self.seller._add_assets.assert_not_called()

    def test_process_transaction_rollback_on_disbursement_failure(self):
        """Test rollback if Bank transfer to Buyer fails"""
        # Arrange
        tx = Transaction(
            buyer_id=3,
            seller_id=4,
            item_id="unit_101",
            price=10000.0,
            quantity=1.0,
            market_id="housing",
            transaction_type="purchase",
            time=100
        )

        # Simulate Bank having insufficient reserves for disbursement
        # First call to transfer (Bank->Buyer) returns False/None
        # Wait, assert_any_call doesn't care about order. I need to mock side_effect.

        def transfer_side_effect(debit, credit, amount, memo, tick=0):
            if debit == self.simulation.bank and credit == self.buyer:
                return None # Fail
            return True # Succeed for others

        self.simulation.settlement_system.transfer.side_effect = transfer_side_effect

        # Act
        self.housing_system.process_transaction(tx, self.simulation)

        # Assert
        # Should call void_loan
        self.simulation.bank.void_loan.assert_called_with("loan_123")

        # Should NOT call withdraw_for_customer
        self.simulation.bank.withdraw_for_customer.assert_not_called()

        # Should NOT call Payment transfer
        # (Since disbursement failed, we abort)
        # However, checking if buyer -> seller was called
        # self.simulation.settlement_system.transfer(self.buyer, self.seller...)
        # Since I use side_effect, I can check call args
        calls = self.simulation.settlement_system.transfer.call_args_list
        # Check that NO call exists with buyer->seller
        payment_attempts = [call for call in calls if call[0][0] == self.buyer and call[0][1] == self.seller]
        self.assertEqual(len(payment_attempts), 0)

        # Ownership NOT transferred
        self.assertEqual(self.unit.owner_id, 2)

    def test_process_transaction_rollback_on_payment_failure(self):
        """Test rollback if Buyer transfer to Seller fails"""
        # Arrange
        tx = Transaction(
            buyer_id=3,
            seller_id=4,
            item_id="unit_101",
            price=10000.0,
            quantity=1.0,
            market_id="housing",
            transaction_type="purchase",
            time=100
        )

        def transfer_side_effect(debit, credit, amount, memo, tick=0):
            if debit == self.buyer and credit == self.seller:
                return None # Fail payment
            return True # Disbursement succeeds

        self.simulation.settlement_system.transfer.side_effect = transfer_side_effect

        # Act
        self.housing_system.process_transaction(tx, self.simulation)

        # Assert
        # 1. Disbursement happened
        self.simulation.settlement_system.transfer.assert_any_call(
            self.simulation.bank, self.buyer, 8000.0, "loan_disbursement", tick=100
        )

        # 2. Withdraw happened
        self.simulation.bank.withdraw_for_customer.assert_called()

        # 3. Rollback: Refund Bank (Buyer -> Bank)
        self.simulation.settlement_system.transfer.assert_any_call(
            self.buyer, self.simulation.bank, 8000.0, "loan_rollback", tick=100
        )

        # 4. Void Loan
        self.simulation.bank.void_loan.assert_called_with("loan_123")

        # Ownership NOT transferred
        self.assertEqual(self.unit.owner_id, 2)

    def test_process_transaction_government_seller_pass_object(self):
        """Test that if seller is Government, collect_tax is called with Buyer OBJECT"""
        # Arrange
        tx = Transaction(
            buyer_id=3,
            seller_id=-1, # Government
            item_id="unit_101",
            price=10000.0,
            quantity=1.0,
            market_id="housing",
            transaction_type="purchase",
            time=100
        )
        self.simulation.agents.get.return_value = self.simulation.government # Default to gov if not found in dict, but dict handles it

        # Act
        self.housing_system.process_transaction(tx, self.simulation)

        # Assert
        self.simulation.government.collect_tax.assert_called_with(
            10000.0, "asset_sale", self.buyer, 100
        )
        # Ensure it was passed self.buyer (the mock object), not 3 (int)
        call_args = self.simulation.government.collect_tax.call_args
        self.assertIs(call_args[0][2], self.buyer)
