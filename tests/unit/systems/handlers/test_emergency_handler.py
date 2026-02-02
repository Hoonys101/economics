import unittest
from unittest.mock import MagicMock
from simulation.systems.handlers.emergency_handler import EmergencyTransactionHandler
from simulation.models import Transaction
from simulation.systems.api import TransactionContext
from modules.government.taxation.system import TaxIntent

class TestEmergencyTax(unittest.TestCase):
    def test_emergency_buy_includes_tax(self):
        # Setup
        handler = EmergencyTransactionHandler()

        buyer = MagicMock()
        buyer.id = 1
        buyer.inventory = {}

        seller = MagicMock()
        seller.id = 2

        gov = MagicMock()
        gov.id = 999
        gov.record_revenue = MagicMock()

        settlement_system = MagicMock()
        settlement_system.settle_atomic.return_value = True

        taxation_system = MagicMock()
        # Mock calculate_tax_intents to return a tax
        taxation_system.calculate_tax_intents.return_value = [
            TaxIntent(payer_id=1, payee_id=999, amount=0.50, reason="sales_tax_emergency_buy")
        ]

        context = MagicMock(spec=TransactionContext)
        context.settlement_system = settlement_system
        context.taxation_system = taxation_system
        context.government = gov
        context.market_data = {}
        context.time = 1

        tx = Transaction(
            buyer_id=1,
            seller_id=2,
            item_id="basic_food",
            quantity=2.0,
            price=5.0, # Total trade = 10.0
            market_id="system",
            transaction_type="emergency_buy",
            time=1
        )

        # Execute
        success = handler.handle(tx, buyer, seller, context)

        # Verify
        self.assertTrue(success)

        # Check Taxation System call
        taxation_system.calculate_tax_intents.assert_called_once()

        # Check Settlement Atomic call
        settlement_system.settle_atomic.assert_called_once()
        args, _ = settlement_system.settle_atomic.call_args
        debit_agent = args[0]
        credits = args[1]

        self.assertEqual(debit_agent, buyer)

        # Credits should be [(seller, 10.0, "emergency_buy"), (gov, 0.50, "sales_tax_emergency_buy")]
        self.assertEqual(len(credits), 2)

        seller_credit = next((c for c in credits if c[0] == seller), None)
        gov_credit = next((c for c in credits if c[0] == gov), None)

        self.assertIsNotNone(seller_credit)
        self.assertEqual(seller_credit[1], 10.0)

        self.assertIsNotNone(gov_credit)
        self.assertEqual(gov_credit[1], 0.50)

        # Verify Gov Revenue Recorded
        gov.record_revenue.assert_called_once()

if __name__ == "__main__":
    unittest.main()
