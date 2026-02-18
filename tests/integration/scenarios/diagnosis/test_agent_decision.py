import pytest
from unittest.mock import MagicMock
from simulation.models import Order
from simulation.core_agents import Household
from simulation.firms import Firm
from simulation.dtos.api import DecisionInputDTO, MarketSnapshotDTO, HousingMarketSnapshotDTO, LaborMarketSnapshotDTO

def test_household_makes_decision(simple_household):
    """Spec 0: 에이전트가 주문을 생성하는지 검증 (Household)"""
    expected_order = Order(agent_id=simple_household.id, side='BUY', item_id='basic_food', quantity=1.0, price_pennies=int(10.0 * 100), price_limit=10.0, market_id='basic_food')
    simple_household.decision_engine.make_decisions = MagicMock(return_value=([expected_order], None))
    input_dto = DecisionInputDTO(goods_data=[], market_data={}, current_time=1, market_snapshot=MarketSnapshotDTO(tick=1, market_signals={}, housing=HousingMarketSnapshotDTO(for_sale_units=[], units_for_rent=[], avg_rent_price=0.0, avg_sale_price=0.0), loan=None, labor=LaborMarketSnapshotDTO(avg_wage=10.0), market_data={}))
    orders, tactic = simple_household.make_decision(input_dto)
    assert len(orders) == 1
    assert orders[0].side == 'BUY'
    assert orders[0].item_id == 'basic_food'
    assert orders[0].price_limit == 10.0

def test_firm_makes_decision(simple_firm):
    """Spec 0: 에이전트가 주문을 생성하는지 검증 (Firm)"""
    expected_order = Order(agent_id=simple_firm.id, side='SELL', item_id='basic_food', quantity=5.0, price_pennies=int(12.0 * 100), price_limit=12.0, market_id='basic_food')
    simple_firm.decision_engine.make_decisions = MagicMock(return_value=([expected_order], None))
    input_dto = DecisionInputDTO(goods_data=[], market_data={}, current_time=1, market_snapshot=MarketSnapshotDTO(tick=1, market_signals={}, housing=None, loan=None, labor=None, market_data={}))
    orders, tactic = simple_firm.make_decision(input_dto)
    assert len(orders) == 1
    assert orders[0].side == 'SELL'
    assert orders[0].item_id == 'basic_food'