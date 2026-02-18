import pytest
from unittest.mock import MagicMock
from simulation.viewmodels.economic_indicators_viewmodel import EconomicIndicatorsViewModel
from simulation.core_markets import Market
from simulation.markets.order_book_market import OrderBookMarket
from simulation.models import Order

@pytest.fixture
def vm():
    repo = MagicMock()
    return EconomicIndicatorsViewModel(repo)

class TestEconomicIndicatorsViewModel:

    def test_get_wealth_distribution(self, vm, golden_households, golden_firms):
        households = golden_households[:3] if len(golden_households) >= 3 else [MagicMock() for _ in range(3)]
        firms = golden_firms[:2] if len(golden_firms) >= 2 else [MagicMock() for _ in range(2)]
        for h, val in zip(households, [10, 20, 100]):
            h.assets = val
        firms[0].assets = 50
        firms[1].assets = 10
        dist = vm.get_wealth_distribution(households, firms)
        assert 'labels' in dist
        assert 'data' in dist
        assert len(dist['data']) == 10
        assert sum(dist['data']) == 5

    def test_get_needs_distribution(self, vm, golden_households, golden_firms):
        h1 = golden_households[0] if golden_households else MagicMock()
        h2 = golden_households[1] if len(golden_households) > 1 else MagicMock()
        f1 = golden_firms[0] if golden_firms else MagicMock()
        h1.needs = {'food': 10, 'shelter': 5}
        h2.needs = {'food': 20, 'shelter': 15}
        f1.needs = {'liquidity_need': 100.0}
        households = [h1, h2]
        firms = [f1]
        dist = vm.get_needs_distribution(households, firms)
        assert dist['household']['food'] == 15.0
        assert dist['household']['shelter'] == 10.0
        assert dist['firm']['liquidity_need'] == 100.0

    def test_get_sales_by_good(self, vm):
        txs = [{'item_id': 'apple', 'quantity': 10}, {'item_id': 'banana', 'quantity': 5}, {'item_id': 'apple', 'quantity': 5}]
        sales = vm.get_sales_by_good(txs)
        assert sales['apple'] == 15
        assert sales['banana'] == 5

    def test_get_market_order_book(self, vm):
        market = MagicMock(spec=OrderBookMarket)
        market.id = 'test_market'
        market.buy_orders = {'apple': [Order(agent_id=1, side='BUY', market_id='test_market', item_id='apple', quantity=10, price_pennies=int(5 * 100), price_limit=5)]}
        market.sell_orders = {'apple': [Order(agent_id=2, side='SELL', market_id='test_market', item_id='apple', quantity=5, price_pennies=int(6 * 100), price_limit=6)]}
        markets = {'test_market': market}
        book = vm.get_market_order_book(markets)
        assert len(book) == 2
        types = [o['type'] for o in book]
        assert 'BID' in types
        assert 'ASK' in types