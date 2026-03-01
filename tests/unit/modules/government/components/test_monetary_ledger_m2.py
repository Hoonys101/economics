import pytest
from modules.finance.kernel.ledger import MonetaryLedger
from modules.system.api import DEFAULT_CURRENCY
from simulation.models import Transaction

from unittest.mock import MagicMock

class TestMonetaryLedgerM2:
    def test_m2_initialization(self):
        ledger = MonetaryLedger(transaction_log=[], time_provider=MagicMock())
        assert ledger.get_total_m2_pennies() == 0

        ledger.set_expected_m2(1000)
        assert ledger.get_expected_m2_pennies() == 1000

    def test_m2_expansion_and_contraction(self):
        ledger = MonetaryLedger(transaction_log=[], time_provider=MagicMock())
        ledger.set_expected_m2(10000)

        # Simulate Money Creation (Expansion)
        # Assuming ID 0 is Central Bank and ID 10 is Public Agent
        tx_expansion = Transaction(
            buyer_id=0, # CB
            seller_id=10, # Public
            item_id="currency",
            quantity=1,
            price=10.0,
            total_pennies=1000,
            market_id="system",
            transaction_type="money_creation",
            time=1,
            currency=DEFAULT_CURRENCY
        )

        ledger.process_transactions([tx_expansion])

        # M2 = 10000 + 1000 = 11000
        assert ledger.get_expected_m2_pennies() == 11000

        # Simulate Money Destruction (Contraction)
        # Public (10) pays CB (0)
        tx_contraction = Transaction(
            buyer_id=10, # Public
            seller_id=0, # CB
            item_id="currency",
            quantity=1,
            price=5.0,
            total_pennies=500,
            market_id="system",
            transaction_type="money_destruction",
            time=2,
            currency=DEFAULT_CURRENCY
        )

        ledger.process_transactions([tx_contraction])

        # M2 = 11000 - 500 = 10500
        assert ledger.get_expected_m2_pennies() == 10500

    def test_m2_non_negative_anomaly(self):
        """
        Verify that M2 never goes negative even if destroyed > base + issued.
        """
        ledger = MonetaryLedger(transaction_log=[], time_provider=MagicMock())
        ledger.set_expected_m2(100)

        tx_large_destruction = Transaction(
            buyer_id=10,
            seller_id=0,
            item_id="currency",
            quantity=1,
            price=10.0,
            total_pennies=500, # Destroys 500
            market_id="system",
            transaction_type="money_destruction",
            time=1,
            currency=DEFAULT_CURRENCY
        )

        ledger.process_transactions([tx_large_destruction])

        # M2 = 100 + 0 - 500 = -400 -> Should be 0
        # Expected M2 doesn't have the non-negative clamp currently (it's in the actual logic which was removed or changed, let's test correctly based on what is in ledger)
        # We need to test the total_money logic or the fallback
        assert ledger.get_expected_m2_pennies() == 0
