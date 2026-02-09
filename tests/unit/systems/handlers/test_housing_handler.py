import unittest
from unittest.mock import MagicMock, call, PropertyMock, patch
from modules.market.handlers.housing_transaction_handler import HousingTransactionHandler
from simulation.models import Transaction
from simulation.agents.government import Government
from simulation.core_agents import Household
from modules.system.escrow_agent import EscrowAgent

class TestHousingTransactionHandler(unittest.TestCase):
    def setUp(self):
        self.handler = HousingTransactionHandler()

        # Mock State (TransactionContext)
        self.state = MagicMock()
        self.state.time = 100
        self.state.config_module = MagicMock()
        self.state.config_module.MORTGAGE_LTV_RATIO = 0.8
        self.state.config_module.MORTGAGE_TERM_TICKS = 300
        self.state.config_module.MORTGAGE_INTEREST_RATE = 0.05
        # Dictionary for housing config
        self.state.config_module.housing = {"max_ltv_ratio": 0.8, "mortgage_term_ticks": 300}

        # Add configs used in BorrowerProfileDTO construction
        self.state.config_module.WORK_HOURS_PER_DAY = 8.0
        self.state.config_module.TICKS_PER_YEAR = 100.0
        self.state.config_module.ESTIMATED_DEBT_PAYMENT_RATIO = 0.01

        self.state.settlement_system = MagicMock()
        self.state.bank = MagicMock()
        self.state.government = MagicMock(spec=Government)
        self.state.government.id = "GOVERNMENT"
        self.state.transactions = []
        self.state.transaction_queue = []

        # Mock Agents
        self.buyer = MagicMock(spec=Household)
        self.buyer.id = 3
        self.buyer._econ_state = MagicMock()
        self.buyer._bio_state = MagicMock()
        self.buyer._econ_state.assets = 20000.0

        # Handle assets property on Household spec
        type(self.buyer).assets = PropertyMock(return_value=20000.0)
        self.buyer.get_balance.return_value = 20000.0

        self.buyer._econ_state.current_wage = 20.0
        self.buyer.current_wage = 20.0 # Satisfy hasattr checks
        self.buyer._bio_state.is_active = True
        self.buyer._econ_state.owned_properties = []
        self.buyer._econ_state.residing_property_id = None

        self.seller = MagicMock(spec=Household)
        self.seller.id = 4
        self.seller._econ_state = MagicMock()
        self.seller._bio_state = MagicMock()
        self.seller._econ_state.assets = 50000.0
        type(self.seller).assets = PropertyMock(return_value=50000.0)
        self.seller.get_balance.return_value = 50000.0

        self.seller._bio_state.is_active = True
        self.seller._econ_state.owned_properties = [101]

        # Mock Escrow Agent
        self.escrow_agent = MagicMock(spec=EscrowAgent)
        self.escrow_agent.id = 99

        # Populate agents map
        self.state.agents = {
            3: self.buyer,
            4: self.seller,
            99: self.escrow_agent,
            "GOVERNMENT": self.state.government
        }

        # Mock Unit
        self.unit = MagicMock()
        self.unit.id = 101
        self.unit.owner_id = 4
        self.unit.mortgage_id = None
        self.unit.liens = []

        self.state.real_estate_units = [self.unit]

        # Defaults
        self.state.settlement_system.transfer.return_value = True
        self.state.bank.grant_loan.return_value = ({"loan_id": "loan_123"}, MagicMock(transaction_type="credit_creation"))
        self.state.bank.withdraw_for_customer.return_value = True
        self.state.bank.terminate_loan.return_value = MagicMock(transaction_type="credit_destruction")
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

        loan_amount = 8000.0 # 80% LTV of 10000
        down_payment = 2000.0

        # 1. Down Payment (Buyer -> Escrow)
        self.state.settlement_system.transfer.assert_any_call(
            self.buyer, self.escrow_agent, down_payment, f"escrow_hold:down_payment:unit_101", tick=100, currency='USD'
        )

        # 2. Deposit Cleanup (Withdrawal)
        self.state.bank.withdraw_for_customer.assert_called_with(3, loan_amount)

        # 3. Loan Disbursement (Bank -> Escrow)
        self.state.settlement_system.transfer.assert_any_call(
            self.state.bank, self.escrow_agent, loan_amount, f"escrow_hold:loan_proceeds:unit_101", tick=100, currency='USD'
        )

        # 4. Final Settlement (Escrow -> Seller)
        self.state.settlement_system.transfer.assert_any_call(
            self.escrow_agent, self.seller, 10000.0, f"final_settlement:unit_101", tick=100, currency='USD'
        )

        # 5. Mortgage Update
        # self.assertEqual(self.unit.mortgage_id, "loan_123")
        # Check liens instead
        self.assertEqual(len(self.unit.liens), 1)
        self.assertEqual(self.unit.liens[0]['loan_id'], "loan_123")

    def test_handle_disbursement_failure(self):
        # Testing failure at Loan Disbursement (Bank -> Escrow)
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

        # Sequence of transfer results:
        # 1. Down Payment (Buyer->Escrow): True
        # 2. Disbursement (Bank->Escrow): False
        # 3. Compensation (Escrow->Buyer): True
        self.state.settlement_system.transfer.side_effect = [True, False, True]

        success = self.handler.handle(tx, self.buyer, self.seller, self.state)

        self.assertFalse(success)

        # Should call terminate_loan because deposit was withdrawn
        self.state.bank.terminate_loan.assert_called_with("loan_123")

        # Should verify deposit was withdrawn before failure
        self.state.bank.withdraw_for_customer.assert_called()

        # Mortgage ID should not be set
        self.assertIsNone(self.unit.mortgage_id)

    def test_handle_payment_failure(self):
        # Testing failure at Final Settlement (Escrow -> Seller)
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

        # Sequence:
        # 1. Down Payment (Buyer->Escrow): True
        # 2. Disbursement (Bank->Escrow): True
        # 3. Final Settlement (Escrow->Seller): False
        # 4. Compensation 1 (Escrow->Bank, Loan): True
        # 5. Compensation 2 (Escrow->Buyer, Down): True
        self.state.settlement_system.transfer.side_effect = [True, True, False, True, True]

        success = self.handler.handle(tx, self.buyer, self.seller, self.state)

        self.assertFalse(success)

        # Verify loan termination
        self.state.bank.terminate_loan.assert_called_with("loan_123")

        # Verify call arguments for compensation
        calls = self.state.settlement_system.transfer.call_args_list
        # Note: 'calls' contains all calls.
        # 0: Down Payment
        # 1: Disbursement (Bank->Escrow)
        # 2: Final Settlement (Failed)
        # 3: Compensation 1 (Escrow->Bank)
        # 4: Compensation 2 (Escrow->Buyer)

        self.assertEqual(calls[3][0][0], self.escrow_agent)
        self.assertEqual(calls[3][0][1], self.state.bank)
        self.assertEqual(calls[3][0][2], 8000.0)

        self.assertEqual(calls[4][0][0], self.escrow_agent)
        self.assertEqual(calls[4][0][1], self.buyer)
        self.assertEqual(calls[4][0][2], 2000.0)

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

        # Pass government as seller
        success = self.handler.handle(tx, self.buyer, self.state.government, self.state)

        self.assertTrue(success)

        # Verify transfer to Government
        self.state.settlement_system.transfer.assert_any_call(
            self.escrow_agent, self.state.government, 10000.0, f"final_settlement:unit_101", tick=100, currency='USD'
        )
