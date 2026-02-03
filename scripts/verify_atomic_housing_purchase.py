import sys
import os
import unittest
from unittest.mock import MagicMock, ANY
from uuid import uuid4

# Add root to path
sys.path.append(os.getcwd())

from modules.housing.dtos import HousingTransactionSagaStateDTO
from modules.finance.saga_handler import HousingTransactionSagaHandler
from simulation.models import Transaction

class TestAtomicHousingPurchase(unittest.TestCase):
    def setUp(self):
        self.simulation = MagicMock()
        self.simulation.time = 1

        # Setup Settlement System
        self.settlement_system = MagicMock()
        self.simulation.settlement_system = self.settlement_system

        # Setup Registry
        self.registry = MagicMock()
        self.simulation.registry = self.registry

        # Setup Bank
        self.bank = MagicMock()
        self.simulation.bank = self.bank
        self.bank.id = 999

        # Setup Loan Market
        self.loan_market = MagicMock()
        self.simulation.markets = {"loan": self.loan_market}

        # Setup Agents
        self.buyer = MagicMock()
        self.buyer.id = 101
        self.buyer.current_wage = 5000.0

        self.seller = MagicMock()
        self.seller.id = 202

        self.simulation.agents = {
            101: self.buyer,
            202: self.seller
        }

        # Setup Handler
        self.handler = HousingTransactionSagaHandler(self.simulation)

    def test_saga_success_flow(self):
        print("\n--- Testing Saga Success Flow ---")
        saga_id = uuid4()
        saga: HousingTransactionSagaStateDTO = {
            "saga_id": saga_id,
            "status": "INITIATED",
            "buyer_id": 101,
            "seller_id": 202,
            "property_id": 500,
            "offer_price": 100000.0,
            "down_payment_amount": 20000.0,
            "loan_application": None,
            "mortgage_approval": None,
            "error_message": None
        }

        # 1. Initiated -> Loan Approved
        # Mock Loan Approval
        self.loan_market.request_mortgage.return_value = {
            "loan_id": 777,
            "approved_principal": 80000.0,
            "monthly_payment": 500.0
        }

        saga = self.handler.execute_step(saga)
        self.assertEqual(saga['status'], "LOAN_APPROVED")
        self.assertIsNotNone(saga['loan_application'])
        self.assertIsNotNone(saga['mortgage_approval'])
        print("Step 1 (Loan Approval): PASS")

        # 2. Loan Approved -> Down Payment Complete
        # Mock Settlement Transfer (Success)
        self.settlement_system.transfer.return_value = Transaction(
            buyer_id=101, seller_id=202, item_id="currency", quantity=20000, price=1, market_id="settlement", transaction_type="transfer", time=1
        )

        saga = self.handler.execute_step(saga)
        self.assertEqual(saga['status'], "DOWN_PAYMENT_COMPLETE")
        self.settlement_system.transfer.assert_called_with(
            debit_agent=self.buyer,
            credit_agent=self.seller,
            amount=20000.0,
            memo=ANY,
            tick=1
        )
        print("Step 2 (Down Payment): PASS")

        # 3. Down Payment -> Mortgage Disbursement
        # Mock Disbursement (Success)
        self.settlement_system.transfer.reset_mock()
        self.settlement_system.transfer.return_value = Transaction(
            buyer_id=101, seller_id=202, item_id="currency", quantity=80000, price=1, market_id="settlement", transaction_type="transfer", time=1
        )

        saga = self.handler.execute_step(saga)
        self.assertEqual(saga['status'], "MORTGAGE_DISBURSEMENT_COMPLETE")
        # Check transfer from Buyer to Seller (since loan proceeds are deposited to buyer)
        self.settlement_system.transfer.assert_called_with(
            debit_agent=self.buyer,
            credit_agent=self.seller,
            amount=80000.0,
            memo=ANY,
            tick=1
        )
        print("Step 3 (Disbursement): PASS")

        # 4. Disbursement -> Completed (Ownership Transfer)
        saga = self.handler.execute_step(saga)
        self.assertEqual(saga['status'], "COMPLETED")
        self.registry.update_ownership.assert_called()
        print("Step 4 (Completion): PASS")

    def test_saga_loan_rejection(self):
        print("\n--- Testing Loan Rejection ---")
        saga: HousingTransactionSagaStateDTO = {
            "saga_id": uuid4(),
            "status": "INITIATED",
            "buyer_id": 101,
            "seller_id": 202,
            "property_id": 500,
            "offer_price": 100000.0,
            "down_payment_amount": 20000.0,
            "loan_application": None,
            "mortgage_approval": None,
            "error_message": None
        }

        # Mock Rejection
        self.loan_market.request_mortgage.return_value = None

        saga = self.handler.execute_step(saga)
        self.assertEqual(saga['status'], "LOAN_REJECTED")
        print("Loan Rejection: PASS")

    def test_saga_rollback_down_payment_fail(self):
        print("\n--- Testing Rollback (Down Payment Fail) ---")
        saga: HousingTransactionSagaStateDTO = {
            "saga_id": uuid4(),
            "status": "LOAN_APPROVED",
            "buyer_id": 101,
            "seller_id": 202,
            "property_id": 500,
            "offer_price": 100000.0,
            "down_payment_amount": 20000.0,
            "loan_application": {"applicant_id": 101, "principal": 80000, "property_id": 500, "property_value": 100000, "loan_term": 360},
            "mortgage_approval": {"loan_id": 777, "approved_principal": 80000, "monthly_payment": 500},
            "error_message": None
        }

        # Mock Transfer Failure
        self.settlement_system.transfer.return_value = None

        saga = self.handler.execute_step(saga)
        self.assertEqual(saga['status'], "FAILED_ROLLED_BACK")
        # Should call void_loan (or terminate_loan)
        self.bank.void_loan.assert_called_with(777)
        print("Rollback (Down Payment Fail): PASS")

    def test_saga_rollback_disbursement_fail(self):
        print("\n--- Testing Rollback (Disbursement Fail) ---")
        saga: HousingTransactionSagaStateDTO = {
            "saga_id": uuid4(),
            "status": "DOWN_PAYMENT_COMPLETE",
            "buyer_id": 101,
            "seller_id": 202,
            "property_id": 500,
            "offer_price": 100000.0,
            "down_payment_amount": 20000.0,
            "loan_application": {},
            "mortgage_approval": {"loan_id": 777, "approved_principal": 80000, "monthly_payment": 500},
            "error_message": None
        }

        # Mock Disbursement Failure
        self.settlement_system.transfer.return_value = None

        saga = self.handler.execute_step(saga)
        self.assertEqual(saga['status'], "FAILED_ROLLED_BACK")

        # Should refund down payment
        self.settlement_system.transfer.assert_called_with(
            debit_agent=self.seller,
            credit_agent=self.buyer,
            amount=20000.0,
            memo=ANY,
            tick=1
        )
        # Should void loan
        self.bank.void_loan.assert_called_with(777)
        print("Rollback (Disbursement Fail): PASS")

    def test_saga_seller_resolution(self):
        print("\n--- Testing Seller Resolution ---")
        saga: HousingTransactionSagaStateDTO = {
            "saga_id": uuid4(),
            "status": "INITIATED",
            "buyer_id": 101,
            "seller_id": -1, # Needs resolution
            "property_id": 500,
            "offer_price": 100000.0,
            "down_payment_amount": 20000.0,
            "loan_application": None,
            "mortgage_approval": None,
            "error_message": None
        }

        # Setup Unit
        unit = MagicMock()
        unit.id = 500
        unit.owner_id = 303
        self.simulation.real_estate_units = [unit]

        # We need request_mortgage to succeed to proceed
        self.loan_market.request_mortgage.return_value = {"loan_id": 1, "approved_principal": 80000, "monthly_payment": 500}

        saga = self.handler.execute_step(saga)
        self.assertEqual(saga['seller_id'], 303)
        self.assertEqual(saga['status'], "LOAN_APPROVED")
        print("Seller Resolution: PASS")

if __name__ == '__main__':
    unittest.main()
