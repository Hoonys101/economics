import unittest
from unittest.mock import MagicMock
from simulation.systems.handlers.goods_handler import GoodsTransactionHandler
from simulation.systems.handlers.inheritance_handler import InheritanceHandler
from simulation.models import Transaction
from simulation.systems.api import TransactionContext
from simulation.systems.settlement_system import SettlementSystem
from modules.finance.api import PortfolioDTO, PortfolioAsset
from modules.system.api import DEFAULT_CURRENCY

class TestEconomicAudit(unittest.TestCase):
    def test_sales_tax_atomicity(self):
        # Setup context
        settlement = SettlementSystem() # Use real settlement logic for atomic behavior
        government = MagicMock()
        government.id = 999
        government.assets = 0.0
        # Mock deposit/withdraw for government too as SettlementSystem calls them
        government.deposit = MagicMock(side_effect=lambda amount, currency=DEFAULT_CURRENCY: setattr(government, 'assets', government.assets + amount))

        taxation_system = MagicMock()
        # Assume tax rate 10%
        intent = MagicMock()
        intent.amount = 10.0
        intent.reason = "sales_tax_goods"
        intent.payer_id = 1 # Buyer
        intent.payee_id = 999 # Gov
        taxation_system.calculate_tax_intents.return_value = [intent]

        context = MagicMock()
        context.settlement_system = settlement
        context.government = government
        context.taxation_system = taxation_system
        context.time = 1

        handler = GoodsTransactionHandler()

        # Setup buyer with 105 (Needs 100 + 10 = 110)
        buyer = MagicMock()
        buyer.id = 1
        buyer.assets = 105.0 # Insufficient
        # Implement mock deposit/withdraw
        def withdraw(amount, currency=DEFAULT_CURRENCY):
             if buyer.assets < amount:
                 raise Exception("InsufficientFunds")
             buyer.assets -= amount
        buyer.withdraw = MagicMock(side_effect=withdraw)
        buyer.deposit = MagicMock(side_effect=lambda amount, currency=DEFAULT_CURRENCY: setattr(buyer, 'assets', buyer.assets + amount))

        seller = MagicMock()
        seller.id = 2
        seller.assets = 0.0
        seller.withdraw = MagicMock() # Should not be called
        seller.deposit = MagicMock(side_effect=lambda amount, currency=DEFAULT_CURRENCY: setattr(seller, 'assets', seller.assets + amount))

        tx = Transaction(
            buyer_id=1, seller_id=2, item_id="item_1", quantity=1, price=100.0,
            market_id="goods", transaction_type="goods", time=1
        )

        # ACT
        result = handler.handle(tx, buyer, seller, context)

        # ASSERT
        self.assertFalse(result, "Transaction should fail atomically due to insufficient funds for tax")
        self.assertEqual(buyer.assets, 105.0, "Buyer assets should remain unchanged")
        self.assertEqual(seller.assets, 0.0, "Seller assets should remain unchanged")
        print("Sales Tax Atomicity Test Passed (Buyer assets preserved)")

    def test_inheritance_leak_stocks(self):
        # Setup context
        settlement = SettlementSystem()
        context = MagicMock()
        context.settlement_system = settlement
        context.time = 1
        government = MagicMock()
        government.id = 999
        government.assets = 0.0
        government.deposit = MagicMock()
        context.government = government # Dust sweeper

        handler = InheritanceHandler()

        # Setup Deceased (Buyer) with Stocks
        # We need to make sure isinstance(deceased, IPortfolioHandler) returns True.
        # Ideally we use a class that implements it, or ensure mock has all methods.
        class MockAgent:
            def __init__(self):
                self.id = 1
                self.assets = 1000.0
                self.portfolio = PortfolioDTO(assets=[
                    PortfolioAsset(asset_type="stock", asset_id="FIRM_1", quantity=10.0)
                ])
                self.get_portfolio = MagicMock(return_value=self.portfolio)
                self.clear_portfolio = MagicMock()
                self.receive_portfolio = MagicMock()

            def withdraw(self, amount, currency=DEFAULT_CURRENCY):
                self.assets -= amount

        deceased = MockAgent()


        # Setup Heir
        heir = MockAgent()
        heir.id = 2
        heir.assets = 0.0
        heir.deposit = MagicMock(side_effect=lambda amount, currency=DEFAULT_CURRENCY: setattr(heir, 'assets', heir.assets + amount))

        context.agents = {2: heir}

        tx = Transaction(
            buyer_id=1, seller_id=None, item_id="estate_distribution", quantity=1, price=1000.0,
            market_id="system", transaction_type="inheritance_distribution", time=1,
            metadata={"heir_ids": [2]}
        )

        # ACT
        result = handler.handle(tx, deceased, None, context)

        # ASSERT
        self.assertTrue(result, "Inheritance handler failed")

        # Verify Cash Transfer (should work)
        self.assertAlmostEqual(heir.assets, 1000.0, msg="Heir received cash")

        # Verify Stocks Transferred (This is expected to FAIL currently)
        try:
            deceased.get_portfolio.assert_called()
            deceased.clear_portfolio.assert_called()
            heir.receive_portfolio.assert_called()
            # Verify payload
            args = heir.receive_portfolio.call_args[0][0]
            self.assertEqual(args.assets[0].quantity, 10.0)
            print("Inheritance Leak Test Passed (Stocks transferred)")
        except AssertionError as e:
            print(f"Inheritance Leak Test FAILED: {e}")
            raise

if __name__ == '__main__':
    unittest.main()
