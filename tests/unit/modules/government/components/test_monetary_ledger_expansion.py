import unittest
from unittest.mock import MagicMock
from modules.government.components.monetary_ledger import MonetaryLedger
from simulation.models import Transaction
from modules.system.api import DEFAULT_CURRENCY
from modules.system.constants import ID_PUBLIC_MANAGER

class TestMonetaryLedgerExpansion(unittest.TestCase):
    def setUp(self):
        self.ledger = MonetaryLedger()
        self.ledger.reset_tick_flow()

    def test_lender_of_last_resort_expansion(self):
        tx = MagicMock(spec=Transaction)
        tx.transaction_type = "lender_of_last_resort"
        tx.price = 5000
        tx.quantity = 1
        tx.total_pennies = 5000 # Pennies (matches expectation of 5000 units)
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
        tx.total_pennies = 10000 # Pennies (matches expectation of 10000 units)
        tx.currency = DEFAULT_CURRENCY
        tx.buyer_id = ID_PUBLIC_MANAGER # ID_PUBLIC_MANAGER
        tx.seller_id = "some_seller"

        self.ledger.process_transactions([tx])

        self.assertEqual(self.ledger.total_money_issued[DEFAULT_CURRENCY], 10000)
        self.assertEqual(self.ledger.credit_delta_this_tick[DEFAULT_CURRENCY], 10000)

    def test_other_types_no_expansion(self):
        tx = MagicMock(spec=Transaction)
        tx.transaction_type = "goods"
        tx.price = 100
        tx.quantity = 1
        tx.total_pennies = 100
        tx.currency = DEFAULT_CURRENCY
        tx.buyer_id = "some_buyer"
        tx.seller_id = "some_seller"

        self.ledger.process_transactions([tx])

        self.assertEqual(self.ledger.total_money_issued[DEFAULT_CURRENCY], 0)
        self.assertEqual(self.ledger.credit_delta_this_tick.get(DEFAULT_CURRENCY, 0), 0)

    def test_bond_repayment_principal_logic(self):
        # Case 1: Principal present in metadata (Partial Contraction)
        tx1 = MagicMock(spec=Transaction)
        tx1.transaction_type = "bond_repayment"
        tx1.total_pennies = 10500 # 10000 Principal + 500 Interest
        tx1.currency = DEFAULT_CURRENCY
        tx1.seller_id = ID_PUBLIC_MANAGER # Money going TO System (Contraction)
        tx1.buyer_id = "household_1"
        tx1.metadata = {'principal': 10000}

        # Case 2: Principal missing (Full Contraction)
        tx2 = MagicMock(spec=Transaction)
        tx2.transaction_type = "bond_repayment"
        tx2.total_pennies = 2000
        tx2.currency = DEFAULT_CURRENCY
        tx2.seller_id = ID_PUBLIC_MANAGER
        tx2.buyer_id = "household_2"
        tx2.metadata = {} # Empty metadata

        # Case 3: Metadata None (Full Contraction)
        tx3 = MagicMock(spec=Transaction)
        tx3.transaction_type = "bond_repayment"
        tx3.total_pennies = 3000
        tx3.currency = DEFAULT_CURRENCY
        tx3.seller_id = ID_PUBLIC_MANAGER
        tx3.buyer_id = "household_3"
        tx3.metadata = None

        # Case 4: Invalid Principal Type (Full Contraction fallback)
        tx4 = MagicMock(spec=Transaction)
        tx4.transaction_type = "bond_repayment"
        tx4.total_pennies = 4000
        tx4.currency = DEFAULT_CURRENCY
        tx4.seller_id = ID_PUBLIC_MANAGER
        tx4.buyer_id = "household_4"
        tx4.metadata = {'principal': "invalid"}

        self.ledger.process_transactions([tx1, tx2, tx3, tx4])

        # Tx1: Contraction = 10000 (Principal)
        # Tx2: Contraction = 2000 (Total)
        # Tx3: Contraction = 3000 (Total)
        # Tx4: Contraction = 4000 (Total)
        expected_contraction = 10000 + 2000 + 3000 + 4000 # = 19000

        self.assertEqual(self.ledger.total_money_destroyed[DEFAULT_CURRENCY], 19000)
        self.assertEqual(self.ledger.credit_delta_this_tick[DEFAULT_CURRENCY], -19000)
