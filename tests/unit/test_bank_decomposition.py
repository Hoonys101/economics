import unittest
from unittest.mock import MagicMock, Mock
from simulation.bank import Bank
from modules.common.config_manager.api import ConfigManager
from modules.system.api import DEFAULT_CURRENCY
from simulation.models import Transaction
from modules.finance.system import FinanceSystem
import config

if not hasattr(config, 'TICKS_PER_YEAR'):
    config.TICKS_PER_YEAR = 48

class TestBankDecomposition(unittest.TestCase):
    def setUp(self):
        self.config_manager = MagicMock(spec=ConfigManager)
        self.config_manager.get.return_value = 0.05

        self.settlement_system = MagicMock()
        def mock_transfer(debit, credit, amount, memo, **kwargs):
            if not isinstance(amount, int):
                raise TypeError(f"Transfer amount must be int, got {type(amount)}")
            return Transaction(
                buyer_id=debit.id, seller_id=credit.id, item_id="test", quantity=1, price=amount, market_id="test", transaction_type="transfer", time=kwargs.get('tick', 0)
            )
        self.settlement_system.transfer.side_effect = mock_transfer

        # Int initial assets
        self.bank = Bank(id=1, initial_assets=10000, config_manager=self.config_manager, settlement_system=self.settlement_system)

        # Inject FinanceSystem
        self.finance_system = Mock(spec=FinanceSystem)
        self.bank.set_finance_system(self.finance_system)

        # Setup common finance system mocks
        self.finance_system.process_loan_application.return_value = (
            {"loan_id": "loan_1", "borrower_id": 101, "original_amount": 0}, []
        )
        self.finance_system.service_debt.return_value = []
        self.finance_system.get_customer_balance.return_value = 0

        # If get_outstanding_loans_for_agent is used, mock it too.
        # But Bank doesn't seem to expose it directly in the new code I read, only get_debt_status.
        # But test_default_processing used it. Let's see if I removed that part.
        # I removed "loans = self.bank.get_outstanding_loans_for_agent(borrower_id)" from my proposed new test code.
        # Bank.get_debt_status returns DebtStatusDTO.

        self.agent = MagicMock()
        self.agent.id = 101
        # Configure wallet mock - return int
        self.agent.wallet.get_balance.return_value = 1000
        self.agent.assets = {DEFAULT_CURRENCY: 1000}

    def test_grant_loan_delegation(self):
        amount = 500  # Int
        interest_rate = 0.05
        borrower_id = 101

        # Mock finance_system response
        mock_dto = {"loan_id": "loan_1", "borrower_id": borrower_id, "original_amount": amount, "principal": amount}
        mock_tx = MagicMock()
        self.finance_system.process_loan_application.return_value = (mock_dto, [mock_tx])

        # Also mock get_customer_balance to reflect the loan deposit if bank.get_customer_balance is called
        self.finance_system.get_customer_balance.return_value = amount

        dto, tx = self.bank.grant_loan(borrower_id, amount, interest_rate)

        self.assertIsNotNone(dto)
        self.assertEqual(dto['borrower_id'], borrower_id)
        self.assertEqual(dto['original_amount'], amount)

        # Verify delegation
        self.finance_system.process_loan_application.assert_called_with(
            borrower_id=borrower_id,
            amount=amount,
            borrower_profile={'preferred_lender_id': self.bank.id},
            current_tick=0
        )

        # Use correct API for customer deposit balance
        balance = self.bank.get_customer_balance(borrower_id)
        self.assertEqual(balance, amount)

    def test_run_tick_interest_collection(self):
        borrower_id = 101

        # Mock service_debt to return interest transaction
        interest_tx = Transaction(
            buyer_id=borrower_id, seller_id=1, item_id="interest", quantity=1, price=10,
            market_id="finance", transaction_type="loan_interest", time=1
        )
        self.finance_system.service_debt.return_value = [interest_tx]

        agents_dict = {borrower_id: self.agent}
        txs = self.bank.run_tick(agents_dict, current_tick=1)

        interest_txs = [tx for tx in txs if tx.transaction_type == 'loan_interest']
        self.assertTrue(len(interest_txs) > 0)
        self.assertEqual(interest_txs[0].buyer_id, borrower_id)
        self.assertEqual(interest_txs[0].seller_id, 1)

        self.finance_system.service_debt.assert_called_with(1)

    def test_default_processing(self):
        # This test checks for 'credit_destruction' transaction which usually happens on default/liquidation
        # We need to mock service_debt to return a credit_destruction tx

        default_tx = Transaction(
            buyer_id=101, seller_id=1, item_id="default", quantity=1, price=1000,
            market_id="finance", transaction_type="credit_destruction", time=2
        )
        self.finance_system.service_debt.return_value = [default_tx]

        agents_dict = {101: self.agent}
        txs = self.bank.run_tick(agents_dict, current_tick=2)

        default_txs = [tx for tx in txs if tx.transaction_type == 'credit_destruction']
        self.assertTrue(len(default_txs) > 0)

        self.finance_system.service_debt.assert_called_with(2)

if __name__ == '__main__':
    unittest.main()
