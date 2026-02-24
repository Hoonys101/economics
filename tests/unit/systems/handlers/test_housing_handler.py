import unittest
from unittest.mock import MagicMock, call, PropertyMock, patch, create_autospec
from modules.market.handlers.housing_transaction_handler import HousingTransactionHandler
from modules.market.api import IHousingTransactionParticipant
from modules.common.interfaces import IPropertyOwner, IResident
from simulation.models import Transaction
from simulation.agents.government import Government
from simulation.core_agents import Household
from modules.system.escrow_agent import EscrowAgent
from modules.system.api import DEFAULT_CURRENCY
from modules.system.constants import ID_GOVERNMENT

class DummyHousingParticipant(IHousingTransactionParticipant, IResident):
    id = 3
    current_wage = 20.0
    owned_properties = []
    residing_property_id = None
    is_homeless = True
    def get_balance(self, currency): return 2000000 # Pennies
    def add_property(self, pid): pass
    def remove_property(self, pid): pass
    def deposit(self, amt, currency): pass
    def withdraw(self, amt, currency): pass

class DummySeller(IPropertyOwner):
    id = 4
    owned_properties = [101]
    def get_balance(self, currency): return 5000000 # Pennies
    def add_property(self, pid): pass
    def remove_property(self, pid): pass
    def deposit(self, amt, currency): pass
    def withdraw(self, amt, currency): pass

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
        # Mock settle_atomic to succeed by default
        self.state.settlement_system.settle_atomic.return_value = True

        self.state.bank = MagicMock()
        self.state.government = MagicMock(spec=Government)
        self.state.government.id = ID_GOVERNMENT
        self.state.transactions = []
        self.state.transaction_queue = []

        # Mock TaxationSystem
        self.state.taxation_system = MagicMock()
        self.state.taxation_system.calculate_tax_intents.return_value = [] # No tax by default

        # Mock Agents
        self.buyer = create_autospec(DummyHousingParticipant, instance=True)
        self.buyer.id = 3
        self.buyer.get_balance.return_value = 2000000 # Pennies
        self.buyer.current_wage = 20.0
        self.buyer.owned_properties = []
        self.buyer.residing_property_id = None
        self.buyer.is_homeless = True

        self.seller = create_autospec(DummySeller, instance=True)
        self.seller.id = 4
        self.seller.get_balance.return_value = 5000000 # Pennies
        self.seller.owned_properties = [101]

        # Mock Escrow Agent
        self.escrow_agent = MagicMock(spec=EscrowAgent)
        self.escrow_agent.id = 99

        # Populate agents map
        self.state.agents = {
            3: self.buyer,
            4: self.seller,
            99: self.escrow_agent,
            ID_GOVERNMENT: self.state.government
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
        mock_loan_dto = MagicMock()
        mock_loan_dto.loan_id = "loan_123"
        self.state.bank.grant_loan.return_value = (mock_loan_dto, MagicMock(transaction_type="credit_creation"))
        self.state.bank.withdraw_for_customer.return_value = True
        self.state.bank.terminate_loan.return_value = MagicMock(transaction_type="credit_destruction")
        self.state.bank.void_loan.return_value = MagicMock(transaction_type="credit_destruction")
        mock_debt_status = MagicMock()
        mock_debt_status.total_outstanding_pennies = 0
        self.state.bank.get_debt_status.return_value = mock_debt_status

    def test_handle_purchase_success(self):
        tx = Transaction(
            buyer_id=3,
            seller_id=4,
            item_id="unit_101",
            price=10000.0,
            quantity=1.0,
            market_id="housing",
            transaction_type="housing",
            time=100,
            total_pennies=1000000
        )

        success = self.handler.handle(tx, self.buyer, self.seller, self.state)

        self.assertTrue(success)

        loan_amount = 800000 # 80% LTV of 1,000,000
        down_payment = 200000 # 20%

        # 1. Down Payment + Tax (Buyer -> Escrow)
        # Tax is 0 in default mock
        self.state.settlement_system.transfer.assert_any_call(
            self.buyer, self.escrow_agent, down_payment, f"escrow_hold:down_payment_tax:unit_101", tick=100, currency=DEFAULT_CURRENCY
        )

        # 2. Deposit Cleanup (Withdrawal)
        self.state.bank.withdraw_for_customer.assert_called_with(3, loan_amount)

        # 3. Loan Disbursement (Bank -> Escrow)
        self.state.settlement_system.transfer.assert_any_call(
            self.state.bank, self.escrow_agent, loan_amount, f"escrow_hold:loan_proceeds:unit_101", tick=100, currency=DEFAULT_CURRENCY
        )

        # 4. Final Settlement (Atomic)
        # Should call settle_atomic with Seller credit
        expected_credits = [(self.seller, 1000000, f"final_settlement:unit_101")]
        self.state.settlement_system.settle_atomic.assert_called_with(
            self.escrow_agent, expected_credits, 100
        )

        # 5. Mortgage Update
        # self.assertEqual(self.unit.mortgage_id, "loan_123")
        # Check liens instead
        self.assertEqual(len(self.unit.liens), 1)
        self.assertEqual(self.unit.liens[0].loan_id, "loan_123")

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
            time=100,
            total_pennies=1000000
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
        # Testing failure at Final Settlement (Atomic)
        tx = Transaction(
            buyer_id=3,
            seller_id=4,
            item_id="unit_101",
            price=10000.0,
            quantity=1.0,
            market_id="housing",
            transaction_type="housing",
            time=100,
            total_pennies=1000000
        )

        # 1. Down Payment: True
        # 2. Disbursement: True
        self.state.settlement_system.transfer.side_effect = [True, True, True, True]
        # Compensation calls will follow if atomic fails.

        # 3. Atomic Settlement: False
        self.state.settlement_system.settle_atomic.return_value = False

        success = self.handler.handle(tx, self.buyer, self.seller, self.state)

        self.assertFalse(success)

        # Verify settle_atomic called
        self.state.settlement_system.settle_atomic.assert_called()

        # Verify loan termination
        self.state.bank.terminate_loan.assert_called_with("loan_123")

        # Verify compensation transfers (Escrow->Bank, Escrow->Buyer)
        # Note: settle_atomic failure triggers 2 compensation transfers.
        # Down Payment (1) + Disbursement (1) + Compensation (2) = 4 transfer calls
        self.assertEqual(self.state.settlement_system.transfer.call_count, 4)

        calls = self.state.settlement_system.transfer.call_args_list
        # 2: Compensation 1 (Escrow->Bank)
        # 3: Compensation 2 (Escrow->Buyer)

        self.assertEqual(calls[2][0][0], self.escrow_agent)
        self.assertEqual(calls[2][0][1], self.state.bank)
        self.assertEqual(calls[2][0][2], 800000)

        self.assertEqual(calls[3][0][0], self.escrow_agent)
        self.assertEqual(calls[3][0][1], self.buyer)
        self.assertEqual(calls[3][0][2], 200000) # Down payment (tax is 0)

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
            time=100,
            total_pennies=1000000
        )

        # Pass government as seller
        success = self.handler.handle(tx, self.buyer, self.state.government, self.state)

        self.assertTrue(success)

        # Verify atomic settlement with Gov as Seller
        expected_credits = [(self.state.government, 1000000, f"final_settlement:unit_101")]
        self.state.settlement_system.settle_atomic.assert_called_with(
            self.escrow_agent, expected_credits, 100
        )
