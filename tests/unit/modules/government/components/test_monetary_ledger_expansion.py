import unittest
from unittest.mock import MagicMock
from modules.government.components.monetary_ledger import MonetaryLedger
from simulation.models import Transaction
from modules.system.api import DEFAULT_CURRENCY

class TestMonetaryLedgerExpansion(unittest.TestCase):
    def setUp(self):
        self.ledger = MonetaryLedger()
        self.ledger.reset_tick_flow()

    def test_lender_of_last_resort_expansion(self):
        tx = MagicMock(spec=Transaction)
        tx.transaction_type = "lender_of_last_resort"
        tx.price = 5000
        tx.quantity = 1
        tx.currency = DEFAULT_CURRENCY
        tx.buyer_id = "some_buyer"
        tx.seller_id = "some_seller"

        self.ledger.process_transactions([tx])

        self.assertEqual(self.ledger.total_money_issued[DEFAULT_CURRENCY], 5000)
        self.assertEqual(self.ledger.credit_delta_this_tick[DEFAULT_CURRENCY], 5000)

    def test_asset_liquidation_expansion(self):
        tx = MagicMock(spec=Transaction)
        tx.transaction_type = "asset_liquidation"
        tx.price = 10000
        tx.quantity = 1
        tx.currency = DEFAULT_CURRENCY
        tx.buyer_id = "4" # ID_PUBLIC_MANAGER
        tx.seller_id = "some_seller"

        self.ledger.process_transactions([tx])

        self.assertEqual(self.ledger.total_money_issued[DEFAULT_CURRENCY], 10000)
        self.assertEqual(self.ledger.credit_delta_this_tick[DEFAULT_CURRENCY], 10000)

    def test_other_types_no_expansion(self):
        tx = MagicMock(spec=Transaction)
        tx.transaction_type = "goods"
        tx.price = 100
        tx.quantity = 1
        tx.currency = DEFAULT_CURRENCY
        tx.buyer_id = "some_buyer"
        tx.seller_id = "some_seller"

        self.ledger.process_transactions([tx])

        self.assertEqual(self.ledger.total_money_issued[DEFAULT_CURRENCY], 0)
        self.assertEqual(self.ledger.credit_delta_this_tick.get(DEFAULT_CURRENCY, 0), 0)
