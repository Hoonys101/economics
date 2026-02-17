import unittest
from simulation.markets.matching_engine import OrderBookMatchingEngine
from modules.market.api import OrderBookStateDTO, CanonicalOrderDTO
from simulation.models import Transaction

class TestPrecisionMatching(unittest.TestCase):
    def test_market_zero_sum_integer(self):
        engine = OrderBookMatchingEngine()

        # Buy @ 100 pennies (1.00)
        buy_order = CanonicalOrderDTO(
            agent_id="buyer",
            side="BUY",
            item_id="item1",
            quantity=1.0,
            price_pennies=100,
            price_limit=1.00,
            market_id="test"
        )

        # Sell @ 99 pennies (0.99)
        sell_order = CanonicalOrderDTO(
            agent_id="seller",
            side="SELL",
            item_id="item1",
            quantity=1.0,
            price_pennies=99,
            price_limit=0.99,
            market_id="test"
        )

        state = OrderBookStateDTO(
            buy_orders={"item1": [buy_order]},
            sell_orders={"item1": [sell_order]},
            market_id="test"
        )

        result = engine.match(state, current_tick=1)

        self.assertEqual(len(result.transactions), 1)
        tx = result.transactions[0]

        # Mid price: (100 + 99) // 2 = 199 // 2 = 99 pennies
        # Total pennies: 99 * 1.0 = 99

        self.assertEqual(tx.total_pennies, 99)
        self.assertEqual(tx.price, 99.0 / 1.0) # 99.0

    def test_market_fractional_qty_rounding(self):
        engine = OrderBookMatchingEngine()

        # Buy @ 10 pennies, Qty 0.33
        buy_order = CanonicalOrderDTO(
            agent_id="buyer",
            side="BUY",
            item_id="item1",
            quantity=0.33,
            price_pennies=10,
            price_limit=0.10,
            market_id="test"
        )

        # Sell @ 10 pennies, Qty 0.33
        sell_order = CanonicalOrderDTO(
            agent_id="seller",
            side="SELL",
            item_id="item1",
            quantity=0.33,
            price_pennies=10,
            price_limit=0.10,
            market_id="test"
        )

        state = OrderBookStateDTO(
            buy_orders={"item1": [buy_order]},
            sell_orders={"item1": [sell_order]},
            market_id="test"
        )

        result = engine.match(state, current_tick=1)

        tx = result.transactions[0]

        # Mid price: (10 + 10) // 2 = 10
        # Total pennies: int(10 * 0.33) = int(3.3) = 3 pennies

        self.assertEqual(tx.total_pennies, 3)
        self.assertAlmostEqual(tx.price, 3 / 0.33, places=5) # ~9.0909...

    def test_labor_market_pricing(self):
        # Labor market uses Buyer's Bid as price
        engine = OrderBookMatchingEngine()

        # Buy Labor @ 1000 pennies
        buy_order = CanonicalOrderDTO(
            agent_id="buyer",
            side="BUY",
            item_id="labor_1",
            quantity=1.0,
            price_pennies=1000,
            price_limit=10.00,
            market_id="labor"
        )

        # Sell Labor @ 900 pennies
        sell_order = CanonicalOrderDTO(
            agent_id="seller",
            side="SELL",
            item_id="labor_1",
            quantity=1.0,
            price_pennies=900,
            price_limit=9.00,
            market_id="labor"
        )

        state = OrderBookStateDTO(
            buy_orders={"labor_1": [buy_order]},
            sell_orders={"labor_1": [sell_order]},
            market_id="labor"
        )

        result = engine.match(state, current_tick=1)

        tx = result.transactions[0]

        # Rule: Trade Price = Buyer's Price (1000)
        self.assertEqual(tx.total_pennies, 1000)

if __name__ == '__main__':
    unittest.main()
