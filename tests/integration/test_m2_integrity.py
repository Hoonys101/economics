import unittest
from unittest.mock import MagicMock
from simulation.models import Transaction
from modules.government.components.monetary_ledger import MonetaryLedger
from modules.system.api import DEFAULT_CURRENCY

class TestM2Integrity(unittest.TestCase):
    def setUp(self):
        self.ledger = MonetaryLedger()
        self.ledger.reset_tick_flow()

    def test_internal_transfers_are_neutral(self):
        """
        Verify that loan_interest, deposit_interest, and bank_profit_remittance
        do NOT cause expansion or contraction in the ledger.
        """
        # 1. Loan Interest (Agent -> Bank)
        tx_interest = Transaction(
            buyer_id=101, seller_id="bank", item_id="loan_1", quantity=1, price=100.0,
            market_id="financial", transaction_type="loan_interest", time=1
        , total_pennies=10000)
        self.ledger.process_transactions([tx_interest])

        delta = self.ledger.get_monetary_delta()
        self.assertEqual(delta, 0.0, "Loan Interest should be Neutral (0.0 delta)")

        # 2. Deposit Interest (Bank -> Agent)
        tx_dep_int = Transaction(
            buyer_id="bank", seller_id=101, item_id="dep_1", quantity=1, price=50.0,
            market_id="financial", transaction_type="deposit_interest", time=1
        , total_pennies=5000)
        self.ledger.process_transactions([tx_dep_int])

        delta = self.ledger.get_monetary_delta()
        self.assertEqual(delta, 0.0, "Deposit Interest should be Neutral")

        # 3. Bank Profit Remittance (Bank -> Gov)
        tx_remit = Transaction(
            buyer_id="bank", seller_id="government", item_id="bank_profit", quantity=1, price=50.0,
            market_id="financial", transaction_type="bank_profit_remittance", time=1
        , total_pennies=5000)
        self.ledger.process_transactions([tx_remit])

        delta = self.ledger.get_monetary_delta()
        self.assertEqual(delta, 0.0, "Bank Profit Remittance should be Neutral")

    def test_credit_creation_expansion(self):
        """Verify credit creation is still expansion."""
        tx_create = Transaction(
            buyer_id="bank", seller_id=-1, item_id="loan_new", quantity=1, price=1000.0,
            market_id="monetary_policy", transaction_type="credit_creation", time=1
        , total_pennies=100000)
        self.ledger.process_transactions([tx_create])

        delta = self.ledger.get_monetary_delta()
        self.assertEqual(delta, 100000, "Credit Creation should be Expansion (Pennies)")

    def test_credit_destruction_contraction(self):
        """Verify credit destruction is still contraction."""
        tx_destroy = Transaction(
            buyer_id=-1, seller_id="bank", item_id="loan_repay", quantity=1, price=500.0,
            market_id="monetary_policy", transaction_type="credit_destruction", time=1
        , total_pennies=50000)
        self.ledger.process_transactions([tx_destroy])

        delta = self.ledger.get_monetary_delta()
        self.assertEqual(delta, -50000, "Credit Destruction should be Contraction (Pennies)")

if __name__ == '__main__':
    unittest.main()
