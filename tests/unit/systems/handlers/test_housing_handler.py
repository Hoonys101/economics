import unittest
from unittest.mock import MagicMock
from modules.market.handlers.housing_transaction_handler import HousingTransactionHandler
from simulation.models import Transaction
from simulation.agents.government import Government
from simulation.core_agents import Household

class TestHousingTransactionHandler(unittest.TestCase):
    def setUp(self):
        self.handler = HousingTransactionHandler()

        # Mock State
        self.state = MagicMock()
        self.state.time = 100
        self.state.config_module = MagicMock()
        self.state.config_module.MORTGAGE_LTV_RATIO = 0.8
        self.state.config_module.MORTGAGE_TERM_TICKS = 300
        self.state.config_module.MORTGAGE_INTEREST_RATE = 0.05
        # Add configs used in BorrowerProfileDTO construction
        self.state.config_module.WORK_HOURS_PER_DAY = 8.0
        self.state.config_module.TICKS_PER_YEAR = 100.0
        self.state.config_module.ESTIMATED_DEBT_PAYMENT_RATIO = 0.01

        self.state.settlement_system = MagicMock()
        self.state.bank = MagicMock()
        self.state.government = MagicMock(spec=Government)
        self.state.government.id = "GOVERNMENT"
        self.state.transactions = []

        # Mock Agents
        self.buyer = MagicMock(spec=Household)
        self.buyer.id = 3
        self.buyer._econ_state = MagicMock()
        self.buyer._bio_state = MagicMock()
        self.buyer._econ_state.assets = 20000.0
        self.buyer._econ_state.current_wage = 20.0 # Needed for income calc
        self.buyer._bio_state.is_active = True
        self.buyer._econ_state.owned_properties = []
        self.buyer._econ_state.residing_property_id = None

        self.seller = MagicMock(spec=Household)
        self.seller.id = 4
        self.seller._econ_state = MagicMock()
        self.seller._bio_state = MagicMock()
        self.seller._econ_state.assets = 50000.0
        self.seller._bio_state.is_active = True
        self.seller._econ_state.owned_properties = [101]

        # Mock Unit
        self.unit = MagicMock()
        self.unit.id = 101
        self.unit.owner_id = 4
        self.unit.mortgage_id = None

        self.state.real_estate_units = [self.unit]

        # Defaults
        self.state.settlement_system.transfer.return_value = True
        self.state.bank.grant_loan.return_value = ({"loan_id": "loan_123"}, MagicMock(transaction_type="credit_creation"))
        self.state.bank.withdraw_for_customer.return_value = True
        self.state.bank.void_loan.return_value = MagicMock(transaction_type="credit_destruction")
        self.state.bank.get_debt_status.return_value = {"total_outstanding_debt": 0.0}

    def test_handle_purchase_success(self):
        tx = Transaction(
            buyer_id=3,
            seller_id=4,
            item_id="unit_101",
            price=10000.0,
            quantity=1.0,
            market_id="housing",
            transaction_type="housing",
            time=100
        )

        success = self.handler.handle(tx, self.buyer, self.seller, self.state)

        self.assertTrue(success)

        # 1. Loan Disbursement
        loan_amount = 8000.0
        self.state.settlement_system.transfer.assert_any_call(
            self.state.bank, self.buyer, loan_amount, "loan_disbursement", tick=100
        )

        # 2. Deposit Cleanup
        self.state.bank.withdraw_for_customer.assert_called_with(3, loan_amount)

        # 3. Payment
        self.state.settlement_system.transfer.assert_any_call(
            self.buyer, self.seller, 10000.0, "purchase_unit_101", tick=100
        )

        # 4. Mortgage Update (Handler does this)
        self.assertEqual(self.unit.mortgage_id, "loan_123")

        # Ownership update is done by Registry, not Handler, so verify Handler did NOT update ownership
        # self.unit.owner_id should still be 4 (Seller)
        self.assertEqual(self.unit.owner_id, 4)

    def test_handle_disbursement_failure(self):
        tx = Transaction(
            buyer_id=3,
            seller_id=4,
            item_id="unit_101",
            price=10000.0,
            quantity=1.0,
            market_id="housing",
            transaction_type="housing",
            time=100
        )

        def transfer_side_effect(debit, credit, amount, memo, tick=0):
            if debit == self.state.bank and credit == self.buyer:
                return False
            return True

        self.state.settlement_system.transfer.side_effect = transfer_side_effect

        success = self.handler.handle(tx, self.buyer, self.seller, self.state)

        self.assertFalse(success)
        self.state.bank.void_loan.assert_called_with("loan_123")
        self.state.bank.withdraw_for_customer.assert_not_called()
        self.assertIsNone(self.unit.mortgage_id)

    def test_handle_payment_failure(self):
        tx = Transaction(
            buyer_id=3,
            seller_id=4,
            item_id="unit_101",
            price=10000.0,
            quantity=1.0,
            market_id="housing",
            transaction_type="housing",
            time=100
        )

        def transfer_side_effect(debit, credit, amount, memo, tick=0):
            if debit == self.buyer and credit == self.seller:
                return False
            return True

        self.state.settlement_system.transfer.side_effect = transfer_side_effect

        success = self.handler.handle(tx, self.buyer, self.seller, self.state)

        self.assertFalse(success)
        # Rollback happened
        self.state.settlement_system.transfer.assert_any_call(
            self.buyer, self.state.bank, 8000.0, "loan_rollback", tick=100
        )
        self.state.bank.void_loan.assert_called_with("loan_123")
        self.assertIsNone(self.unit.mortgage_id)

    def test_handle_government_seller(self):
        tx = Transaction(
            buyer_id=3,
            seller_id=-1,
            item_id="unit_101",
            price=10000.0,
            quantity=1.0,
            market_id="housing",
            transaction_type="housing",
            time=100
        )

        # When seller_id is -1, handler receives seller=None
        # It should resolve to state.government
        self.state.government.collect_tax.return_value = {"success": True}

        success = self.handler.handle(tx, self.buyer, None, self.state)

        self.assertTrue(success)
        self.state.government.collect_tax.assert_called_with(
            10000.0, "asset_sale", self.buyer, 100
        )
