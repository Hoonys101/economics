import pytest
from unittest.mock import MagicMock
from modules.finance.kernel.ledger import MonetaryLedger
from modules.system.api import DEFAULT_CURRENCY

class TestMonetaryLedgerDebt:

    def test_initial_debt_is_zero(self):
        ledger = MonetaryLedger([], MagicMock())
        assert ledger.get_system_debt_pennies(DEFAULT_CURRENCY) == 0

    def test_record_system_debt_increase(self):
        ledger = MonetaryLedger([], MagicMock())
        ledger.record_system_debt_increase(1000, "test_source", DEFAULT_CURRENCY)
        assert ledger.get_system_debt_pennies(DEFAULT_CURRENCY) == 1000

    def test_record_system_debt_decrease(self):
        ledger = MonetaryLedger([], MagicMock())
        ledger.record_system_debt_increase(1000, "test_source", DEFAULT_CURRENCY)
        ledger.record_system_debt_decrease(500, "test_source", DEFAULT_CURRENCY)
        assert ledger.get_system_debt_pennies(DEFAULT_CURRENCY) == 500

    def test_system_debt_underflow_protection(self):
        ledger = MonetaryLedger([], MagicMock())
        ledger.record_system_debt_increase(500, "test_source", DEFAULT_CURRENCY)
        ledger.record_system_debt_decrease(1000, "test_source", DEFAULT_CURRENCY)
        assert ledger.get_system_debt_pennies(DEFAULT_CURRENCY) == 0

    def test_multiple_currencies(self):
        ledger = MonetaryLedger([], MagicMock())
        ledger.record_system_debt_increase(1000, "test_source", "USD")
        ledger.record_system_debt_increase(2000, "test_source", "EUR")

        assert ledger.get_system_debt_pennies("USD") == 1000
        assert ledger.get_system_debt_pennies("EUR") == 2000
