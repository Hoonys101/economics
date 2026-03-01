from unittest.mock import MagicMock
import pytest
from unittest.mock import MagicMock
from modules.finance.kernel.ledger import MonetaryLedger
from simulation.models import Transaction
from modules.system.constants import ID_CENTRAL_BANK

class TestMonetaryLedgerRepayment:
    def test_bond_repayment_split(self):
        """
        Verify that bond repayment uses SSoT (total_pennies) and destroys full amount.
        Split logic removed for Zero-Sum Integrity.
        """
        ledger = MonetaryLedger(transaction_log=[], time_provider=MagicMock())
        ledger.reset_tick_flow()

        # Mock Transaction
        # 1000 Principal, 50 Interest. Total 1050.
        # Seller = Central Bank (so it triggers contraction check)
        tx = MagicMock(spec=Transaction)
        tx.id = "tx-legacy-1"
        tx.transaction_type = "bond_repayment"
        tx.seller_id = ID_CENTRAL_BANK
        tx.buyer_id = "government"
        tx.price = 1050.0
        tx.quantity = 1.0
        tx.total_pennies = 105000 # 1050.00 USD
        tx.currency = "USD"
        tx.metadata = {
            "repayment_details": {
                "principal": 1000.0,
                "interest": 50.0,
                "bond_id": "BOND_1"
            }
        }

        ledger.process_transactions([tx])

        # Check destroyed amount
        # Full amount (105000 pennies) destroyed.
        assert ledger.total_money_destroyed["USD"] == 105000.0
        assert ledger.credit_delta_this_tick["USD"] == -105000.0

    def test_bond_repayment_legacy_fallback(self):
        """
        Verify that bond repayment without metadata destroys full amount.
        """
        ledger = MonetaryLedger(transaction_log=[], time_provider=MagicMock())
        ledger.reset_tick_flow()

        tx = MagicMock(spec=Transaction)
        tx.id = "tx-legacy-2"
        tx.transaction_type = "bond_repayment"
        tx.seller_id = ID_CENTRAL_BANK
        tx.buyer_id = "government"
        tx.price = 1050.0
        tx.quantity = 1.0
        tx.total_pennies = 105000 # 1050.00 USD
        tx.currency = "USD"
        # No metadata or missing repayment_details
        tx.metadata = {}

        ledger.process_transactions([tx])

        # Full amount destroyed
        assert ledger.total_money_destroyed["USD"] == 105000.0
        assert ledger.credit_delta_this_tick["USD"] == -105000.0

    def test_interest_is_not_destroyed(self):
        """
        Verify that interest portion (if part of total_pennies) IS destroyed now,
        as it represents money leaving circulation to System Agent.
        """
        ledger = MonetaryLedger(transaction_log=[], time_provider=MagicMock())
        ledger.reset_tick_flow()

        tx = MagicMock(spec=Transaction)
        tx.transaction_type = "bond_repayment"
        tx.seller_id = ID_CENTRAL_BANK
        tx.buyer_id = "government"
        tx.price = 100.0 # Total payment
        tx.quantity = 1.0
        tx.total_pennies = 10000 # 100.00 USD
        tx.currency = "USD"
        tx.metadata = {
            "repayment_details": {
                "principal": 0.0,
                "interest": 100.0,
                "bond_id": "BOND_X"
            }
        }

        ledger.process_transactions([tx])

        # Full amount destroyed
        assert ledger.total_money_destroyed.get("USD", 0.0) == 10000.0
        assert ledger.credit_delta_this_tick.get("USD", 0.0) == -10000.0
