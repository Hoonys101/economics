import pytest
from unittest.mock import Mock, MagicMock
from pytest import approx
from simulation.markets.circuit_breaker import DynamicCircuitBreaker
from simulation.markets.order_book_market import OrderBookMarket
from modules.market.api import CanonicalOrderDTO

class TestDynamicCircuitBreaker:
    @pytest.fixture
    def config(self):
        config = MagicMock()
        config.PRICE_VOLATILITY_WINDOW_TICKS = 20
        config.CIRCUIT_BREAKER_MIN_HISTORY = 5
        config.MARKET_CIRCUIT_BREAKER_BASE_LIMIT = 0.15
        config.CIRCUIT_BREAKER_TIMEOUT_TICKS = 10
        # Relaxation config is ignored now but we keep it to ensure it doesn't crash
        config.CIRCUIT_BREAKER_RELAXATION_PER_TICK = 0.05
        return config

    def test_bounds_calculation_without_history(self, config):
        cb = DynamicCircuitBreaker(config_module=config)
        lower, upper = cb.get_dynamic_price_bounds("item1", 100, -1)
        assert lower == 0.0
        assert upper == float('inf')

    def test_bounds_calculation_with_history(self, config):
        cb = DynamicCircuitBreaker(config_module=config)
        # Add history: mean=100
        for _ in range(10):
            cb.update_price_history("item1", 100.0)

        lower, upper = cb.get_dynamic_price_bounds("item1", 100, 99)
        # Base limit 0.15. Mean 100.
        # Margin = 15.
        # Lower = 85. Upper = 115.

        assert lower == approx(85.0)
        assert upper == approx(115.0)

    def test_no_temporal_relaxation(self, config):
        """
        Verifies that temporal relaxation logic is REMOVED and bounds remain strict
        even after timeout.
        """
        cb = DynamicCircuitBreaker(config_module=config)
        for _ in range(10):
            cb.update_price_history("item1", 100.0)

        # Timeout is 10. Last trade at 80. Current tick 100.
        # Ticks since = 20.
        # OLD Behavior: Relaxation applied.
        # NEW Behavior: Strict bounds maintained.

        lower, upper = cb.get_dynamic_price_bounds("item1", 100, 80)
        assert lower == approx(85.0) # Was 84.5
        assert upper == approx(115.0) # Was 115.5

class TestOrderBookMarketIntegration:
    @pytest.fixture
    def config(self):
        config = MagicMock()
        config.PRICE_VOLATILITY_WINDOW_TICKS = 20
        config.CIRCUIT_BREAKER_MIN_HISTORY = 5
        config.MARKET_CIRCUIT_BREAKER_BASE_LIMIT = 0.15
        config.CIRCUIT_BREAKER_TIMEOUT_TICKS = 10
        config.CIRCUIT_BREAKER_RELAXATION_PER_TICK = 0.05
        return config

    def test_place_order_delegates_to_circuit_breaker(self, config):
        market = OrderBookMarket("test_market", config_module=config)
        # Note: OrderBookMarket creates its own DynamicCircuitBreaker if not provided

        # Manually populate history in the internal circuit breaker
        for _ in range(10):
            market.circuit_breaker.update_price_history("item1", 100.0)

        # Try place order out of bounds (bounds are [85, 115])
        order = CanonicalOrderDTO(
            agent_id="agent1",
            side="BUY",
            item_id="item1",
            quantity=1.0,
            price_pennies=12000,
            market_id="test_market",
            price_limit=120.0
        )

        # Should reject (log warning) and not add to orders
        market.place_order(order, 100)
        assert len(market._buy_orders.get("item1", [])) == 0

        # Try place order within bounds
        order_valid = CanonicalOrderDTO(
            agent_id="agent1",
            side="BUY",
            item_id="item1",
            quantity=1.0,
            price_pennies=10000,
            market_id="test_market",
            price_limit=100.0
        )
        market.place_order(order_valid, 100)
        assert len(market._buy_orders.get("item1", [])) == 1
