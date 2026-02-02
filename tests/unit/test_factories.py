import pytest
from unittest.mock import Mock, MagicMock
from simulation.orchestration.factories import MarketSignalFactory, DecisionInputFactory, MarketSnapshotFactory
from simulation.markets.order_book_market import OrderBookMarket
from modules.system.api import (
    MarketSignalDTO, MarketSnapshotDTO, HousingMarketSnapshotDTO,
    LoanMarketSnapshotDTO, LaborMarketSnapshotDTO
)
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
        # Check new fields
        assert signals["item1"].total_bid_quantity == 0.0
        assert signals["item1"].total_ask_quantity == 0.0

class TestMarketSnapshotFactory:
    def test_create_snapshot(self):
        signal_factory = MagicMock(spec=MarketSignalFactory)
        signal_factory.create_market_signals.return_value = {}

        factory = MarketSnapshotFactory(signal_factory)

        state = MagicMock(spec=SimulationState)
        state.time = 50
        state.markets = {}
        state.market_data = {
            "housing_market": {"avg_rent_price": 500.0, "avg_sale_price": 100000.0},
            "loan_market": {"interest_rate": 0.03},
            "labor": {"avg_wage": 20.0}
        }
        state.real_estate_units = []

        snapshot = factory.create_snapshot(state)

        assert isinstance(snapshot, MarketSnapshotDTO)
        assert snapshot.tick == 50

        assert isinstance(snapshot.housing, HousingMarketSnapshotDTO)
        assert snapshot.housing.avg_rent_price == 500.0

        assert isinstance(snapshot.loan, LoanMarketSnapshotDTO)
        assert snapshot.loan.interest_rate == 0.03

        assert isinstance(snapshot.labor, LaborMarketSnapshotDTO)
        assert snapshot.labor.avg_wage == 20.0

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
        # Ensure markets is NOT in dto (if we could check that, but type checker handles it)
        # We can check it's not available
        with pytest.raises(AttributeError):
            _ = dto.markets
