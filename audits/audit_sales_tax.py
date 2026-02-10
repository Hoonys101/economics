
import sys
import os
import unittest
from unittest.mock import MagicMock, ANY

# Adjust path to allow imports
sys.path.append(os.getcwd())

from simulation.systems.handlers.goods_handler import GoodsTransactionHandler
from simulation.models import Transaction
from simulation.systems.api import TransactionContext
from modules.system.api import DEFAULT_CURRENCY

class TestSalesTaxAtomicity(unittest.TestCase):
    def setUp(self):
        self.handler = GoodsTransactionHandler()
        self.buyer = MagicMock()
        self.buyer.id = 101
        self.seller = MagicMock()
        self.seller.id = 102
        self.government = MagicMock()
        self.government.id = 1

        self.settlement_system = MagicMock()
        self.taxation_system = MagicMock()
        self.config = MagicMock()

        self.context = TransactionContext(
            agents={101: self.buyer, 102: self.seller},
            inactive_agents={},
            government=self.government,
            settlement_system=self.settlement_system,
            taxation_system=self.taxation_system,
            stock_market=None,
            real_estate_units=[],
            market_data={},
            config_module=self.config,
            logger=MagicMock(),
            time=0,
            bank=None,
            central_bank=None,
            public_manager=None,
            transaction_queue=[]
        )

    def test_insufficient_funds_for_tax(self):
        """
        Scenario: Buyer has enough for the item price, but not enough for the sales tax.
        Expected: The entire transaction should fail (atomic).
        """
        # Setup
        price = 100.0
        tax_rate = 0.05
        tax_amount = price * tax_rate
        total_cost = price + tax_amount

        # Buyer has exactly the price, but not tax
        self.buyer.get_balance.return_value = 100.0

        # Mock Taxation System to return a tax intent
        mock_intent = MagicMock()
        mock_intent.amount = tax_amount
        mock_intent.reason = "sales_tax"
        mock_intent.payer_id = self.buyer.id
        self.taxation_system.calculate_tax_intents.return_value = [mock_intent]

        # Transaction
        tx = Transaction(
            buyer_id=self.buyer.id,
            seller_id=self.seller.id,
            item_id="good_item",
            quantity=1.0,
            price=price,
            market_id="goods_market",
            transaction_type="goods",
            time=0
        )

        # Mock Settlement System's settle_atomic behavior
        def mock_settle_atomic(debit_agent, credits, tick):
            # Calculate total debit requested
            total_debit = sum(amount for _, amount, _ in credits)

            # Check funds (simulating real settlement logic)
            balance = debit_agent.get_balance(DEFAULT_CURRENCY)
            if balance < total_debit:
                return False
            return True

        self.settlement_system.settle_atomic.side_effect = mock_settle_atomic

        # Execute
        result = self.handler.handle(tx, self.buyer, self.seller, self.context)

        # Verify
        self.assertFalse(result, "Transaction should fail due to insufficient funds for tax")

        # Verify settle_atomic was called with correct arguments
        self.settlement_system.settle_atomic.assert_called_once()
        call_args = self.settlement_system.settle_atomic.call_args
        credits = call_args[0][1]

        # Expect credits for Seller and Government
        seller_credit = next((c for c in credits if c[0] == self.seller), None)
        gov_credit = next((c for c in credits if c[0] == self.government), None)

        self.assertIsNotNone(seller_credit)
        self.assertEqual(seller_credit[1], 100.0)

        self.assertIsNotNone(gov_credit)
        self.assertEqual(gov_credit[1], 5.0)

        print("\nAUDIT PASSED: Sales Tax Atomicity verified.")

if __name__ == '__main__':
    unittest.main()
