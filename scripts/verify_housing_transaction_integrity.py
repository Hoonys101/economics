import sys
import os
import unittest
from unittest.mock import MagicMock, ANY
from uuid import uuid4

# Add root to path
sys.path.append(os.getcwd())

from simulation.systems.settlement_system import SettlementSystem
from modules.market.housing_purchase_api import HousingPurchaseSagaDTO, HousingPurchaseSagaDataDTO
from modules.market.housing_planner_api import MortgageApplicationDTO
from simulation.models import Transaction

class TestAtomicHousingPurchaseV3(unittest.TestCase):
    def setUp(self):
        # Mock Simulation State
        self.simulation_state = MagicMock()
        self.simulation_state.time = 1

        # Setup Agents
        # Use spec to prevent MagicMock from creating 'finance' or '_econ_state' attributes which confuse SettlementSystem
        self.buyer = MagicMock(spec=['id', 'assets', 'deposit', 'withdraw'])
        self.buyer.id = 101
        self.buyer.assets = 50000.0 # Enough for down payment

        self.seller = MagicMock(spec=['id', 'assets', 'deposit', 'withdraw'])
        self.seller.id = 202
        self.seller.assets = 0.0

        # Bank needs to avoid 'finance' attr too, and have all methods used
        self.bank = MagicMock(spec=['id', 'assets', 'deposit', 'withdraw', 'withdraw_for_customer', 'get_balance', 'terminate_loan', 'stage_loan', 'get_interest_rate', 'get_debt_status'])
        self.bank.id = 999
        self.bank.assets = 10000000.0 # Give bank liquidity
        self.bank.withdraw_for_customer.return_value = True # Allow seamless withdrawal

        self.government = MagicMock(spec=['id', 'assets', 'deposit', 'withdraw'])
        self.government.id = 0

        self.agents = {
            101: self.buyer,
            202: self.seller,
            0: self.government
        }
        self.simulation_state.agents = self.agents
        self.simulation_state.government = self.government

        # Setup Property
        self.unit = MagicMock()
        self.unit.id = 500
        self.unit.owner_id = 202
        self.unit.estimated_value = 100000.0
        self.simulation_state.real_estate_units = [self.unit]
        self.simulation_state.transactions = []

        # Setup Markets
        self.loan_market = MagicMock()
        self.simulation_state.markets = {"loan_market": self.loan_market}

        # Setup Settlement System
        self.settlement_system = SettlementSystem(logger=MagicMock(), bank=self.bank)
        self.simulation_state.settlement_system = self.settlement_system

    def test_saga_success_flow(self):
        print("\n--- Testing Saga Success Flow (Atomic V3) ---")

        # 1. Setup Saga
        saga_id = str(uuid4())
        mortgage_app = MortgageApplicationDTO(
            applicant_id=101,
            principal=80000.0,
            purpose="MORTGAGE",
            property_id=500,
            property_value=100000.0,
            applicant_income=60000.0,
            applicant_existing_debt=0.0,
            loan_term=360
        )
        saga_data = HousingPurchaseSagaDataDTO(
            household_id=101,
            property_id=500,
            offer_price=100000.0,
            down_payment=20000.0,
            mortgage_application=mortgage_app,
            approved_loan_id=None,
            seller_id=202
        )
        saga = HousingPurchaseSagaDTO(
            saga_id=saga_id,
            saga_type="HOUSING_PURCHASE",
            status="STARTED",
            current_step=0,
            data=saga_data,
            start_tick=self.simulation_state.time
        )

        # 2. Submit Saga
        self.settlement_system.submit_saga(saga)
        self.assertIn(saga_id, self.settlement_system.sagas)
        print("Saga Submitted: PASS")

        # 3. Process Tick T (Loan Approval)
        # Mock Loan Approval
        self.loan_market.apply_for_mortgage.return_value = {"loan_id": 777}

        self.settlement_system.process_sagas(self.simulation_state)

        updated_saga = self.settlement_system.sagas[saga_id]
        self.assertEqual(updated_saga['status'], "LOAN_APPROVED")
        self.assertEqual(updated_saga['data']['approved_loan_id'], 777)
        print("Tick T (Loan Approval): PASS")

        # 4. Process Tick T+1 (Settlement)
        self.simulation_state.time += 1

        # Mock Bank Transaction for Multiparty Settlement
        # We need execute_multiparty_settlement to work.
        # It calls transfer which calls _execute_withdrawal -> bank.withdraw_for_customer or agent.withdraw
        # Buyer pays Seller offer_price (100k). Buyer receives 80k from Bank.
        # Buyer pays 20k from assets.

        # Mock Bank deposit/withdraw behavior on agents?
        # SettlementSystem uses agent.withdraw/deposit.
        # We need to make sure agents update assets or mock methods call logic.

        def deposit(amount):
            self.buyer.assets += amount
        def withdraw(amount):
            self.buyer.assets -= amount
        self.buyer.deposit = MagicMock(side_effect=deposit)
        self.buyer.withdraw = MagicMock(side_effect=withdraw)

        self.seller.deposit = MagicMock()

        self.settlement_system.process_sagas(self.simulation_state)

        # Check completion
        self.assertNotIn(saga_id, self.settlement_system.sagas) # Should be archived/removed

        # Check Registry
        self.assertEqual(self.unit.owner_id, 101)
        self.assertEqual(self.unit.mortgage_id, "777")
        print("Tick T+1 (Settlement & Registry Update): PASS")

    def test_saga_rejection_dti(self):
        print("\n--- Testing Saga Rejection (DTI) ---")
        saga_id = str(uuid4())
        mortgage_app = MortgageApplicationDTO(
            applicant_id=101,
            principal=80000.0,
            purpose="MORTGAGE",
            property_id=500,
            property_value=100000.0,
            applicant_income=10000.0, # Low income
            applicant_existing_debt=0.0,
            loan_term=360
        )
        saga_data = HousingPurchaseSagaDataDTO(
            household_id=101,
            property_id=500,
            offer_price=100000.0,
            down_payment=20000.0,
            mortgage_application=mortgage_app,
            approved_loan_id=None,
            seller_id=202
        )
        saga = HousingPurchaseSagaDTO(
            saga_id=saga_id,
            saga_type="HOUSING_PURCHASE",
            status="STARTED",
            current_step=0,
            data=saga_data,
            start_tick=self.simulation_state.time
        )

        self.settlement_system.submit_saga(saga)

        # Mock Loan Rejection
        self.loan_market.apply_for_mortgage.return_value = None

        self.settlement_system.process_sagas(self.simulation_state)

        # Check Rejection
        self.assertNotIn(saga_id, self.settlement_system.sagas)
        # Verify no property transfer
        self.assertEqual(self.unit.owner_id, 202)
        print("Loan Rejection: PASS")

if __name__ == '__main__':
    unittest.main()
