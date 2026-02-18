import pytest
from unittest.mock import MagicMock
from collections import deque, defaultdict
from modules.household.engines.belief_engine import BeliefEngine
from modules.household.engines.crisis_engine import CrisisEngine
from modules.household.api import BeliefInputDTO, PanicSellingInputDTO
from simulation.models import Share

class TestBeliefEngine:

    def test_update_beliefs_basic(self):
        engine = BeliefEngine()
        perceived_prices = {'apple': 10.0}
        expected_inflation = {'apple': 0.0}
        price_history = defaultdict(lambda: deque(maxlen=10))
        price_history['apple'].append(10.0)
        market_data = {'goods_market': {'apple_avg_traded_price': 12.0}}
        config = MagicMock()
        config.perceived_price_update_factor = 0.5
        input_dto = BeliefInputDTO(current_tick=1, perceived_prices=perceived_prices, expected_inflation=expected_inflation, price_history=price_history, adaptation_rate=0.1, goods_info_map={'apple': {}}, config=config, market_data=market_data)
        result = engine.update_beliefs(input_dto)
        assert result.new_perceived_prices['apple'] == 11.0
        assert abs(result.new_expected_inflation['apple'] - 0.02) < 1e-06
        assert len(price_history['apple']) == 2
        assert price_history['apple'][-1] == 12.0

class TestCrisisEngine:

    def test_evaluate_distress_portfolio(self):
        engine = CrisisEngine()
        share = Share(firm_id=1, holder_id=100, quantity=10, acquisition_price=10.0)
        portfolio_holdings = {1: share}
        input_dto = PanicSellingInputDTO(owner_id=100, portfolio_holdings=portfolio_holdings, inventory={})
        result = engine.evaluate_distress(input_dto)
        assert len(result.orders) == 1
        order = result.orders[0]
        assert order.side == 'SELL'
        assert order.item_id == 'stock_1'
        assert order.quantity == 10
        assert order.agent_id == 100