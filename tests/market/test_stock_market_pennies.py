import unittest
from simulation.markets.matching_engine import StockMatchingEngine
from modules.market.api import StockMarketStateDTO, CanonicalOrderDTO
from simulation.models import Transaction

class TestStockMarketPennies(unittest.TestCase):
    def test_stock_matching_integer_math(self):
        engine = StockMatchingEngine()

        # Buy 1 share @ 1000 pennies ($10.00)
        buy_order = CanonicalOrderDTO(
            agent_id="buyer_firm",
            side="BUY",
            item_id="stock_101",
            quantity=1.0,
            price_pennies=1000,
            price_limit=10.00,
            market_id="stock_market"
        )

        # Sell 1 share @ 900 pennies ($9.00)
        sell_order = CanonicalOrderDTO(
            agent_id="seller_firm",
            side="SELL",
            item_id="stock_101",
            quantity=1.0,
            price_pennies=900,
            price_limit=9.00,
            market_id="stock_market"
        )

        # State setup
        state = StockMarketStateDTO(
            buy_orders={101: [buy_order]},
            sell_orders={101: [sell_order]},
            market_id="stock_market"
        )

        result = engine.match(state, current_tick=100)

        # Assertions
        self.assertEqual(len(result.transactions), 1)
        tx = result.transactions[0]

        # Mid Price: (1000 + 900) // 2 = 1900 // 2 = 950 pennies
        expected_price_pennies = 950

        self.assertEqual(tx.total_pennies, expected_price_pennies)
        self.assertEqual(tx.transaction_type, "stock")
        # Ensure float price is consistent for display
        self.assertEqual(tx.price, 9.50)

    def test_stock_matching_fractional_shares(self):
        engine = StockMatchingEngine()

        # Buy 0.5 shares @ 2000 pennies ($20.00)
        buy_order = CanonicalOrderDTO(
            agent_id="buyer_firm",
            side="BUY",
            item_id="stock_102",
            quantity=0.5,
            price_pennies=2000,
            price_limit=20.00,
            market_id="stock_market"
        )

        # Sell 0.5 shares @ 2000 pennies ($20.00)
        sell_order = CanonicalOrderDTO(
            agent_id="seller_firm",
            side="SELL",
            item_id="stock_102",
            quantity=0.5,
            price_pennies=2000,
            price_limit=20.00,
            market_id="stock_market"
        )

        state = StockMarketStateDTO(
            buy_orders={102: [buy_order]},
            sell_orders={102: [sell_order]},
            market_id="stock_market"
        )

        result = engine.match(state, current_tick=100)

        tx = result.transactions[0]

        # Price: 2000 pennies
        # Total Pennies: int(2000 * 0.5) = 1000
        self.assertEqual(tx.total_pennies, 1000)
        self.assertEqual(tx.quantity, 0.5)
        self.assertEqual(tx.price, 20.00) # effective price per share

if __name__ == '__main__':
    unittest.main()
