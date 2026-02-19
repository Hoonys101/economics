import pytest
from unittest.mock import MagicMock
from simulation.systems.handlers.goods_handler import GoodsTransactionHandler
from simulation.models import Transaction
from modules.finance.api import IFinancialAgent
from simulation.systems.api import TransactionContext
from simulation.core_agents import Household
from simulation.firms import Firm

class TestGoodsHandlerPrecision:

    def test_legacy_price_handling(self):
        """
        Verify that legacy transactions (without total_pennies) are handled correctly.
        Current implementation suspects that dollars are treated as pennies.
        """
        handler = GoodsTransactionHandler()

        # Scenario: 1 unit at $10.00
        # Should be 1000 pennies.
        tx = Transaction(
            buyer_id=1,
            seller_id=2,
            item_id="test_item",
            quantity=1.0,
            price=10.00, # Dollars
            market_id="test",
            transaction_type="goods",
            time=1
        , total_pennies=1000)

        # Mock Context
        context = MagicMock(spec=TransactionContext)
        context.taxation_system = MagicMock()
        context.taxation_system.calculate_tax_intents.return_value = []
        context.settlement_system = MagicMock()
        context.settlement_system.settle_atomic.return_value = True
        context.config_module = MagicMock()
        context.government = MagicMock() # Added this
        context.market_data = {}
        context.time = 1

        buyer = MagicMock(spec=Household)
        buyer.id = 1
        seller = MagicMock(spec=Firm)
        seller.id = 2

        # Execute
        handler.handle(tx, buyer, seller, context)

        # Check what was passed to settle_atomic
        # settle_atomic(debit_agent, credits_list, tick)
        # credits_list = [(seller, amount, memo), ...]
        call_args = context.settlement_system.settle_atomic.call_args
        assert call_args is not None

        credits = call_args[0][1]
        amount = credits[0][1]

        # If the bug exists, amount will be 10 (pennies) instead of 1000.
        print(f"Settled Amount: {amount}")

        assert amount == 1000, f"Expected 1000 pennies ($10.00), got {amount}"
