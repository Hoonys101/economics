import pytest
from unittest.mock import MagicMock
from simulation.markets.order_book_market import OrderBookMarket
from collections import deque

class TestCircuitBreakerRelaxation:
    @pytest.fixture
    def market(self):
        config_mock = MagicMock()
        config_mock.CIRCUIT_BREAKER_MIN_HISTORY = 5
        config_mock.MARKET_CIRCUIT_BREAKER_BASE_LIMIT = 0.15
        config_mock.PRICE_VOLATILITY_WINDOW_TICKS = 20

        market = OrderBookMarket(market_id="test_market", config_module=config_mock, logger=MagicMock())
        return market

    def test_sparse_history_returns_infinite_bounds(self, market):
        # Setup sparse history (e.g. 2 items, less than 5)
        item_id = "apple"
        market._update_price_history(item_id, 10.0)
        market._update_price_history(item_id, 11.0)

        # Verify
        min_p, max_p = market.get_dynamic_price_bounds(item_id)
        assert min_p == 0.0
        assert max_p == float('inf')

    def test_sufficient_history_returns_finite_bounds(self, market):
        # Setup sufficient history (e.g. 5 items)
        item_id = "apple"
        for p in [10.0, 10.5, 9.5, 10.0, 10.0]:
            market._update_price_history(item_id, p)

        # Verify
        min_p, max_p = market.get_dynamic_price_bounds(item_id)
        assert max_p < float('inf')
        assert min_p >= 0.0

    def test_no_history_returns_infinite_bounds(self, market):
        item_id = "unknown"
        min_p, max_p = market.get_dynamic_price_bounds(item_id)
        assert min_p == 0.0
        assert max_p == float('inf')

    def test_default_config_fallback(self):
        # Test without config module
        market = OrderBookMarket(market_id="test_market", config_module=None, logger=MagicMock())
        item_id = "apple"

        # Default is 7. Add 6 items.
        for _ in range(6):
            market._update_price_history(item_id, 10.0)

        min_p, max_p = market.get_dynamic_price_bounds(item_id)
        assert max_p == float('inf') # Should still be infinite (6 < 7)

        # Add 7th item
        market._update_price_history(item_id, 10.0)
        min_p, max_p = market.get_dynamic_price_bounds(item_id)
        assert max_p < float('inf') # Should be finite now (7 >= 7)
