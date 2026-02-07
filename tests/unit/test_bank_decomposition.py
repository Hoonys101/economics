import unittest
from unittest.mock import MagicMock
from simulation.bank import Bank
from modules.common.config_manager.api import ConfigManager
from modules.system.api import DEFAULT_CURRENCY
from simulation.models import Transaction
import config

if not hasattr(config, 'TICKS_PER_YEAR'):
    config.TICKS_PER_YEAR = 48

class TestBankDecomposition(unittest.TestCase):
    def setUp(self):
        self.config_manager = MagicMock(spec=ConfigManager)
        self.config_manager.get.return_value = 0.05

        self.settlement_system = MagicMock()
        def mock_transfer(debit, credit, amount, memo, **kwargs):
            return Transaction(
                buyer_id=debit.id, seller_id=credit.id, item_id="test", quantity=1, price=amount, market_id="test", transaction_type="transfer", time=kwargs.get('tick', 0)
            )
        self.settlement_system.transfer.side_effect = mock_transfer

        self.bank = Bank(id=1, initial_assets=10000.0, config_manager=self.config_manager, settlement_system=self.settlement_system)

        self.agent = MagicMock()
        self.agent.id = 101
        # Configure wallet mock
        self.agent.wallet.get_balance.return_value = 1000.0
        self.agent.assets = {DEFAULT_CURRENCY: 1000.0}

    def test_grant_loan_delegation(self):
        amount = 500.0
        interest_rate = 0.05

        dto, tx = self.bank.grant_loan("101", amount, interest_rate)

        self.assertIsNotNone(dto)
        self.assertEqual(dto['borrower_id'], "101")
        self.assertEqual(dto['original_amount'], amount)

        loan_dto = self.bank.loan_manager.get_loan_by_id(dto['loan_id'])
        self.assertIsNotNone(loan_dto)
        self.assertEqual(loan_dto['principal'], amount)

        balance = self.bank.get_balance("101")
        self.assertEqual(balance, amount)

    def test_run_tick_interest_collection(self):
        amount = 1000.0
        self.bank.grant_loan("101", amount, 0.12)

        agents_dict = {101: self.agent}
        txs = self.bank.run_tick(agents_dict, current_tick=1)

        interest_txs = [tx for tx in txs if tx.transaction_type == 'loan_interest']
        self.assertTrue(len(interest_txs) > 0)
        self.assertEqual(interest_txs[0].buyer_id, 101)
        self.assertEqual(interest_txs[0].seller_id, 1)

        self.settlement_system.transfer.assert_called()

    def test_default_processing(self):
        amount = 10000.0
        res = self.bank.grant_loan("101", amount, 0.12)
        self.assertIsNotNone(res)

        # Agent has no money
        self.agent.wallet.get_balance.return_value = 0.0
        self.agent.assets = {DEFAULT_CURRENCY: 0.0}

        self.settlement_system.transfer.side_effect = None
        self.settlement_system.transfer.return_value = None # Fail transfer

        agents_dict = {101: self.agent}
        txs = self.bank.run_tick(agents_dict, current_tick=2)

        default_txs = [tx for tx in txs if tx.transaction_type == 'credit_destruction']
        if len(default_txs) == 0:
            print(f"NO DEFAULT TX generated. Txs: {[(t.transaction_type, t.price) for t in txs]}")

        self.assertTrue(len(default_txs) > 0)

        loans = self.bank.get_outstanding_loans_for_agent(101)
        total_outstanding = sum(l['amount'] for l in loans)
        self.assertEqual(total_outstanding, 0.0)

if __name__ == '__main__':
    unittest.main()
