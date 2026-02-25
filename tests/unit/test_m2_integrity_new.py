import unittest
from unittest.mock import MagicMock, Mock
from modules.finance.kernel.ledger import MonetaryLedger
from simulation.systems.settlement_system import SettlementSystem
from modules.system.api import DEFAULT_CURRENCY
from simulation.models import Transaction

class TestM2IntegrityNew(unittest.TestCase):
    def setUp(self):
        # Setup mocks
        self.mock_settlement = MagicMock(spec=SettlementSystem)
        self.mock_time_provider = Mock()
        self.mock_time_provider.time = 1
        self.transaction_log = []

        self.ledger = MonetaryLedger(
            transaction_log=self.transaction_log,
            time_provider=self.mock_time_provider,
            settlement_system=self.mock_settlement
        )

    def test_get_total_m2_delegates_to_settlement(self):
        """Verify get_total_m2_pennies calls settlement system."""
        self.mock_settlement.get_total_m2_pennies.return_value = 500000

        m2 = self.ledger.get_total_m2_pennies()

        self.assertEqual(m2, 500000)
        self.mock_settlement.get_total_m2_pennies.assert_called_with(DEFAULT_CURRENCY)

    def test_record_monetary_expansion(self):
        """Verify expansion updates expected M2 and logs transaction."""
        self.ledger.set_expected_m2(100000)

        self.ledger.record_monetary_expansion(50000, "test_expansion")

        self.assertEqual(self.ledger.get_expected_m2_pennies(), 150000)
        self.assertEqual(len(self.transaction_log), 1)
        tx = self.transaction_log[0]
        self.assertEqual(tx.transaction_type, "monetary_expansion")
        self.assertEqual(tx.total_pennies, 50000)
        self.assertTrue(tx.metadata["is_monetary_expansion"])

    def test_record_monetary_contraction(self):
        """Verify contraction updates expected M2 and logs transaction."""
        self.ledger.set_expected_m2(100000)

        self.ledger.record_monetary_contraction(20000, "test_contraction")

        self.assertEqual(self.ledger.get_expected_m2_pennies(), 80000)
        self.assertEqual(len(self.transaction_log), 1)
        tx = self.transaction_log[0]
        self.assertEqual(tx.transaction_type, "monetary_contraction")
        self.assertEqual(tx.total_pennies, 20000)
        self.assertTrue(tx.metadata["is_monetary_destruction"])

if __name__ == '__main__':
    unittest.main()
