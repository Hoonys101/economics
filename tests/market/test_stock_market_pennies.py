import unittest
from simulation.markets.matching_engine import StockMatchingEngine
from modules.market.api import StockMarketStateDTO, CanonicalOrderDTO
from simulation.models import Transaction


class TestStockMarketPennies(unittest.TestCase):

    def test_stock_matching_integer_math(self):
        engine = StockMatchingEngine()
        buy_order = CanonicalOrderDTO(agent_id='buyer_firm', side='BUY',
            item_id='stock_101', quantity=1.0, price_pennies=1000,
            market_id='stock_market')
        sell_order = CanonicalOrderDTO(agent_id='seller_firm', side='SELL',
            item_id='stock_101', quantity=1.0, price_pennies=900, market_id
            ='stock_market')
        state = StockMarketStateDTO(buy_orders={(101): [buy_order]},
            sell_orders={(101): [sell_order]}, market_id='stock_market')
        result = engine.match(state, current_tick=100)
        self.assertEqual(len(result.transactions), 1)
        tx = result.transactions[0]
        expected_price_pennies = 950
        self.assertEqual(tx.total_pennies, expected_price_pennies)
        self.assertEqual(tx.transaction_type, 'stock')
        self.assertEqual(tx.price, 9.5)

    def test_stock_matching_fractional_shares(self):
        engine = StockMatchingEngine()
        buy_order = CanonicalOrderDTO(agent_id='buyer_firm', side='BUY',
            item_id='stock_102', quantity=0.5, price_pennies=2000,
            market_id='stock_market')
        sell_order = CanonicalOrderDTO(agent_id='seller_firm', side='SELL',
            item_id='stock_102', quantity=0.5, price_pennies=2000,
            market_id='stock_market')
        state = StockMarketStateDTO(buy_orders={(102): [buy_order]},
            sell_orders={(102): [sell_order]}, market_id='stock_market')
        result = engine.match(state, current_tick=100)
        tx = result.transactions[0]
        self.assertEqual(tx.total_pennies, 1000)
        self.assertEqual(tx.quantity, 0.5)
        self.assertEqual(tx.price, 20.0)


if __name__ == '__main__':
    unittest.main()
