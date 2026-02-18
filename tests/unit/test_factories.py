import pytest
from unittest.mock import Mock, MagicMock
from simulation.orchestration.factories import MarketSignalFactory, DecisionInputFactory, MarketSnapshotFactory
from simulation.markets.order_book_market import OrderBookMarket
from modules.system.api import MarketSignalDTO, MarketSnapshotDTO, HousingMarketSnapshotDTO, LoanMarketSnapshotDTO, LaborMarketSnapshotDTO, HousingMarketUnitDTO
from simulation.dtos.api import SimulationState, DecisionInputDTO, Order
from simulation.models import RealEstateUnit

class TestMarketSignalFactory:

    def test_create_market_signals(self):
        factory = MarketSignalFactory()
        mock_market = MagicMock(spec=OrderBookMarket)
        mock_market.buy_orders = {'item1': []}
        mock_market.sell_orders = {'item1': []}
        mock_market.last_traded_prices = {'item1': 10.0}
        mock_market.price_history = {'item1': [10.0, 10.0]}
        mock_market.get_best_bid.return_value = 9.0
        mock_market.get_best_ask.return_value = 11.0
        mock_market.get_last_traded_price.return_value = 10.0
        mock_market.get_last_trade_tick.return_value = 1
        markets = {'market1': mock_market}
        signals = factory.create_market_signals(markets)
        assert 'item1' in signals
        assert isinstance(signals['item1'], MarketSignalDTO)
        assert signals['item1'].market_id == 'market1'
        assert signals['item1'].best_bid == 9.0
        assert signals['item1'].total_bid_quantity == 0.0
        assert signals['item1'].total_ask_quantity == 0.0

class TestMarketSnapshotFactory:

    def test_create_snapshot(self):
        signal_factory = MagicMock(spec=MarketSignalFactory)
        signal_factory.create_market_signals.return_value = {}
        factory = MarketSnapshotFactory()
        factory.signal_factory = signal_factory
        state = MagicMock(spec=SimulationState)
        state.time = 50
        state.markets = {}
        state.market_data = {'housing_market': {'avg_rent_price': 500.0, 'avg_sale_price': 100000.0}, 'loan_market': {'interest_rate': 0.03}, 'labor': {'avg_wage': 20.0}}
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

    def test_create_snapshot_with_housing_quality(self):
        factory = MarketSnapshotFactory()
        state = MagicMock(spec=SimulationState)
        state.time = 1
        state.market_data = {}
        mock_housing_market = MagicMock()
        unit_id = 123
        item_id = f'unit_{unit_id}'
        sell_order = Order(agent_id=1, item_id=item_id, price_pennies=int(25000.0 * 100), price_limit=25000.0, quantity=1.0, market_id='housing', side='SELL')
        mock_housing_market.sell_orders = {item_id: [sell_order]}
        state.markets = {'housing': mock_housing_market}
        unit = RealEstateUnit(id=unit_id, condition=0.85, rent_price=120.0)
        state.real_estate_units = [unit]
        snapshot = factory.create_snapshot(state)
        assert isinstance(snapshot.housing, HousingMarketSnapshotDTO)
        assert len(snapshot.housing.for_sale_units) == 1
        unit_dto = snapshot.housing.for_sale_units[0]
        assert isinstance(unit_dto, HousingMarketUnitDTO)
        assert unit_dto.unit_id == item_id
        assert unit_dto.price == 25000.0
        assert unit_dto.quality == 0.85
        assert unit_dto.rent_price == 120.0

class TestDecisionInputFactory:

    def test_create_decision_input(self):
        factory = DecisionInputFactory()
        state = MagicMock(spec=SimulationState)
        state.government = MagicMock()
        state.bank = MagicMock()
        state.central_bank = MagicMock()
        state.config_module = MagicMock()
        state.markets = {}
        state.goods_data = {}
        state.market_data = {}
        state.time = 10
        state.tracker = MagicMock()
        state.tracker.capture_market_context.return_value = MagicMock()
        world_state = MagicMock()
        world_state.stock_tracker = MagicMock()
        world_state.stress_scenario_config = MagicMock()
        market_snapshot = MagicMock(spec=MarketSnapshotDTO)
        dto = factory.create_decision_input(state, world_state, market_snapshot)
        assert isinstance(dto, DecisionInputDTO)
        assert dto.current_time == 10
        assert dto.market_snapshot == market_snapshot
        with pytest.raises(AttributeError):
            _ = dto.markets