import pytest
from unittest.mock import Mock, MagicMock
from simulation.orchestration.factories import MarketSignalFactory, DecisionInputFactory
from simulation.markets.order_book_market import OrderBookMarket
from modules.system.api import MarketSignalDTO, MarketSnapshotDTO
from simulation.dtos.api import SimulationState, DecisionInputDTO

class TestMarketSignalFactory:
    def test_create_market_signals(self):
        factory = MarketSignalFactory()

        # Mock Market
        mock_market = MagicMock(spec=OrderBookMarket)
        # MagicMock isinstance check works if spec is class

        mock_market.buy_orders = {"item1": []}
        mock_market.sell_orders = {"item1": []}
        mock_market.last_traded_prices = {"item1": 10.0}
        mock_market.price_history = {"item1": [10.0, 10.0]}
        mock_market.get_best_bid.return_value = 9.0
        mock_market.get_best_ask.return_value = 11.0
        mock_market.get_last_traded_price.return_value = 10.0
        mock_market.get_last_trade_tick.return_value = 1

        markets = {"market1": mock_market}

        signals = factory.create_market_signals(markets)

        assert "item1" in signals
        assert isinstance(signals["item1"], MarketSignalDTO)
        assert signals["item1"].market_id == "market1"
        assert signals["item1"].best_bid == 9.0

class TestDecisionInputFactory:
    def test_create_decision_input(self):
        factory = DecisionInputFactory()

        # Mock State
        state = MagicMock(spec=SimulationState)
        state.government = MagicMock()
        state.bank = MagicMock()
        state.central_bank = MagicMock()
        state.config_module = MagicMock()
        state.markets = {}
        state.goods_data = {}
        state.market_data = {}
        state.time = 10

        # Mock WorldState
        world_state = MagicMock()
        world_state.stock_tracker = MagicMock()
        world_state.stress_scenario_config = MagicMock()

        market_snapshot = MagicMock(spec=MarketSnapshotDTO)

        dto = factory.create_decision_input(state, world_state, market_snapshot)

        assert isinstance(dto, DecisionInputDTO)
        assert dto.current_time == 10
        assert dto.market_snapshot == market_snapshot
