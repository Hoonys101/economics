import sys
import os
import unittest
from unittest.mock import MagicMock, ANY
from uuid import uuid4

# Add root to path
sys.path.append(os.getcwd())

from modules.finance.sagas.housing_api import HousingTransactionSagaStateDTO, HousingSagaAgentContext, MortgageApprovalDTO
from modules.finance.saga_handler import HousingTransactionSagaHandler
from modules.simulation.api import HouseholdSnapshotDTO
from modules.finance.api import MortgageApplicationDTO
from simulation.models import Transaction

class TestAtomicHousingPurchase(unittest.TestCase):
    def setUp(self):
        self.simulation = MagicMock()
        self.simulation.time = 1

        # Setup Settlement System
        self.settlement_system = MagicMock()
        self.simulation.settlement_system = self.settlement_system

        # Setup Housing Service (InventoryHandler)
        self.housing_service = MagicMock()
        self.simulation.housing_service = self.housing_service
        self.housing_service.lock_asset.return_value = True
        self.housing_service.add_lien.return_value = "lien_123"
        self.housing_service.transfer_asset.return_value = True

        # Setup Bank
        self.bank = MagicMock()
        self.bank.id = 999
        self.simulation.bank = self.bank

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

        # Setup Government
        self.government = MagicMock()
        self.government.id = 0
        self.simulation.government = self.government

        # Setup Handler
        self.handler = HousingTransactionSagaHandler(self.simulation)

    def test_saga_success_flow(self):
        print("\n--- Testing Saga Success Flow ---")
        saga_id = uuid4()

        buyer_ctx = HouseholdSnapshotDTO(
            household_id="101", cash=20000.0, income=60000.0, credit_score=750.0, existing_debt=0.0, assets_value=20000.0
        )
        seller_ctx = HousingSagaAgentContext(
            id=202, monthly_income=0.0, existing_monthly_debt=0.0
        )
        loan_app = MortgageApplicationDTO(
            applicant_id=101, requested_principal=80000.0, purpose="MORTGAGE", property_id=500, property_value=100000.0, applicant_monthly_income=5000.0, existing_monthly_debt_payments=0.0, loan_term=360
        )

        saga = HousingTransactionSagaStateDTO(
            saga_id=saga_id,
            status="INITIATED",
            buyer_context=buyer_ctx,
            seller_context=seller_ctx,
            property_id=500,
            offer_price=100000.0,
            down_payment_amount=20000.0,
            loan_application=loan_app,
            mortgage_approval=None,
            staged_loan_id=None,
            error_message=None,
            last_processed_tick=0,
            logs=[]
        )

        # 1. Initiated -> Credit Check
        # Handler should lock asset and stage mortgage
        self.loan_market.stage_mortgage_application.return_value = "staged_123"

        saga = self.handler.execute_step(saga)
        self.assertEqual(saga.status, "CREDIT_CHECK")
        self.assertEqual(saga.staged_loan_id, "staged_123")
        self.housing_service.lock_asset.assert_called_with(500, saga_id)
        print("Step 1 (Staging): PASS")

        # 2. Credit Check -> Approved
        # Loan Market confirms approval
        self.loan_market.check_staged_application_status.return_value = "APPROVED"

        # Manually reset tick to force processing (handler skips if same tick)
        self.simulation.time = 2
        saga = self.handler.execute_step(saga)
        self.assertEqual(saga.status, "APPROVED")
        print("Step 2 (Credit Check): PASS")

        # 3. Approved -> Escrow Locked
        # Handler converts to loan and adds lien
        loan_info = MagicMock()
        loan_info.loan_id = "loan_777"
        loan_info.approved_principal = 80000.0
        self.loan_market.convert_staged_to_loan.return_value = loan_info

        self.simulation.time = 3
        saga = self.handler.execute_step(saga)
        self.assertEqual(saga.status, "ESCROW_LOCKED")
        self.assertIsNotNone(saga.mortgage_approval)
        self.assertEqual(saga.mortgage_approval.loan_id, "loan_777")
        self.housing_service.add_lien.assert_called()
        print("Step 3 (Approval & Lien): PASS")

        # 4. Escrow Locked -> Transfer Title
        # Handler executes settlement
        self.settlement_system.execute_multiparty_settlement.return_value = True

        self.simulation.time = 4
        saga = self.handler.execute_step(saga)
        self.assertEqual(saga.status, "TRANSFER_TITLE")
        self.settlement_system.execute_multiparty_settlement.assert_called()
        # Verify call args
        call_args = self.settlement_system.execute_multiparty_settlement.call_args
        transfers = call_args[0][0]
        # Check order: Bank->Buyer (Principal), Buyer->Seller (Price)
        # Bank->Buyer: 80000.0 * 100 = 8000000
        # Buyer->Seller: 100000.0 * 100 = 10000000
        self.assertEqual(transfers[0][0], self.bank)
        self.assertEqual(transfers[0][1], self.buyer)
        self.assertEqual(transfers[0][2], 8000000)
        self.assertEqual(transfers[1][0], self.buyer)
        self.assertEqual(transfers[1][1], self.seller)
        self.assertEqual(transfers[1][2], 10000000)
        print("Step 4 (Settlement): PASS")

        # 5. Transfer Title -> Completed
        self.simulation.time = 5
        saga = self.handler.execute_step(saga)
        self.assertEqual(saga.status, "COMPLETED")
        self.housing_service.transfer_asset.assert_called_with(500, 101)
        self.housing_service.release_asset.assert_called_with(500, saga_id)
        print("Step 5 (Title Transfer & Completion): PASS")

if __name__ == '__main__':
    unittest.main()
