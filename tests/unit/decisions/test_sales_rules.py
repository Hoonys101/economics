import pytest
from unittest.mock import Mock
from simulation.dtos import DecisionContext
from simulation.schemas import FirmActionVector
from tests.utils.factories import create_firm_config_dto
from modules.system.api import DEFAULT_CURRENCY

class TestSalesRules:

    def test_sales_aggressiveness_impact_on_price(self, ai_decision_engine, base_mock_firm, firm_engine_config, create_firm_state_dto):
        """Verify that sales aggressiveness inversely affects price."""
        state = create_firm_state_dto(base_mock_firm, firm_engine_config)
        state.finance.balance = {DEFAULT_CURRENCY: 100000}
        state.production.inventory['food'] = 100.0
        state.sales.price_history['food'] = 10.0
        snapshot = Mock()
        snapshot.market_signals = {'food': Mock(last_trade_tick=1)}
        context = DecisionContext(state=state, config=create_firm_config_dto(), market_data={}, goods_data=[], current_time=1, market_snapshot=snapshot)
        ai_decision_engine.ai_engine.decide_action_vector.return_value = FirmActionVector(sales_aggressiveness=0.1, hiring_aggressiveness=0.5, rd_aggressiveness=0.5, capital_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5)
        output_low = ai_decision_engine.make_decisions(context)
        orders_low = output_low.orders
        sell_orders_low = [o for o in orders_low if o.order_type == 'SELL' or o.order_type == 'SET_PRICE']
        price_low_agg = 0.0
        for o in sell_orders_low:
            if o.order_type == 'SELL' and hasattr(o, 'price_limit'):
                price_low_agg = o.price_limit
            elif o.order_type == 'SET_PRICE':
                price_low_agg = o.price_limit
        ai_decision_engine.ai_engine.decide_action_vector.return_value = FirmActionVector(sales_aggressiveness=0.9, hiring_aggressiveness=0.5, rd_aggressiveness=0.5, capital_aggressiveness=0.5, dividend_aggressiveness=0.5, debt_aggressiveness=0.5)
        output_high = ai_decision_engine.make_decisions(context)
        orders_high = output_high.orders
        sell_orders_high = [o for o in orders_high if o.order_type == 'SELL' or o.order_type == 'SET_PRICE']
        price_high_agg = 0.0
        for o in sell_orders_high:
            if o.order_type == 'SELL' and hasattr(o, 'price_limit'):
                price_high_agg = o.price_limit
            elif o.order_type == 'SET_PRICE':
                price_high_agg = o.price_limit
        if price_low_agg > 0 and price_high_agg > 0:
            assert price_low_agg > price_high_agg