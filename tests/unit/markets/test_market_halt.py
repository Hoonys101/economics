import pytest
from unittest.mock import MagicMock
from simulation.markets.order_book_market import OrderBookMarket
from simulation.markets.stock_market import StockMarket
from modules.market.api import IIndexCircuitBreaker, CanonicalOrderDTO, MatchingResultDTO, StockMarketConfigDTO

class TestMarketHalt:
    @pytest.fixture
    def mock_breaker(self):
        breaker = MagicMock(spec=IIndexCircuitBreaker)
        breaker.is_active.return_value = True
        return breaker

    def test_order_book_market_halts(self, mock_breaker):
        market = OrderBookMarket("test_market", circuit_breaker=mock_breaker)
        # Add order to verify it DOES NOT reach matching
        order = CanonicalOrderDTO("agent1", "BUY", "item1", 1.0, 100, "test_market")
        market.place_order(order, 100)

        market.matching_engine = MagicMock()

        transactions = market.match_orders(100)
        assert transactions == []
        mock_breaker.is_active.assert_called()
        market.matching_engine.match.assert_not_called()

    def test_stock_market_halts(self, mock_breaker):
        registry = MagicMock()
        config_dto = StockMarketConfigDTO()
        market = StockMarket(config_dto=config_dto, shareholder_registry=registry, index_circuit_breaker=mock_breaker)
        transactions = market.match_orders(100)
        assert transactions == []
        mock_breaker.is_active.assert_called()

    def test_order_book_market_resumes(self):
        mock_breaker = MagicMock(spec=IIndexCircuitBreaker)
        mock_breaker.is_active.return_value = False
        market = OrderBookMarket("test_market", circuit_breaker=mock_breaker)

        # Place an order so we expect matching to run
        order = CanonicalOrderDTO("agent1", "BUY", "item1", 1.0, 100, "test_market")
        market.place_order(order, 100)

        # Mock matching engine
        market.matching_engine = MagicMock()
        market.matching_engine.match.return_value = MatchingResultDTO([], {}, {}, {})

        market.match_orders(100)
        market.matching_engine.match.assert_called()
