import os
import sys
import json
import pytest
import logging
from unittest.mock import Mock
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import config
from simulation.core_agents import Household, Talent, Personality
from simulation.ai_model import AIEngineRegistry
from simulation.core_markets import Market
from simulation.models import Order
from simulation.markets.order_book_market import OrderBookMarket
from simulation.decisions.action_proposal import ActionProposalEngine
from simulation.ai.state_builder import StateBuilder
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.ai.household_ai import HouseholdAI
from simulation.utils.config_factory import create_config_dto
from modules.simulation.dtos.api import HouseholdConfigDTO
from simulation.ai.enums import Tactic
from simulation.dtos.api import DecisionInputDTO
from modules.simulation.api import AgentCoreConfigDTO
from modules.system.api import MarketSnapshotDTO, HousingMarketSnapshotDTO, LoanMarketSnapshotDTO, LaborMarketSnapshotDTO, MarketSignalDTO
from tests.utils.factories import create_firm_config_dto, create_household_config_dto, create_household

@pytest.fixture
def setup_test_environment():
    """Fixture to set up the test environment."""
    goods_json_path = os.path.join(project_root, 'data', 'goods.json')
    try:
        with open(goods_json_path, 'r', encoding='utf-8') as f:
            goods_data = json.load(f)
    except FileNotFoundError:
        pytest.fail(f'Error: {goods_json_path} not found.')
    markets = {'goods_market': OrderBookMarket('goods_market'), 'labor_market': OrderBookMarket('labor_market'), 'loan_market': Mock(spec=Market)}
    goods_market = markets['goods_market']
    goods_market.place_order(Order(agent_id=99, side='SELL', item_id='basic_food', quantity=100, price_pennies=int(10.0 * 100), price_limit=10.0, market_id='goods_market'), 0)
    goods_market.place_order(Order(agent_id=98, side='SELL', item_id='luxury_food', quantity=50, price_pennies=int(50.0 * 100), price_limit=50.0, market_id='goods_market'), 0)
    return (goods_data, markets)

@pytest.fixture
def ai_engine_setup():
    """Fixture for setting up AI engine components."""
    value_orientation = config.VALUE_ORIENTATION_WEALTH_AND_NEEDS
    action_proposal_engine = ActionProposalEngine(config_module=config, n_action_samples=10)
    state_builder = StateBuilder()
    ai_engine_registry = AIEngineRegistry(action_proposal_engine=action_proposal_engine, state_builder=state_builder)
    return (ai_engine_registry, value_orientation)

def create_mock_snapshot(market_data):
    housing_snapshot = HousingMarketSnapshotDTO(for_sale_units=[], units_for_rent=[], avg_rent_price=100.0, avg_sale_price=24000.0)
    loan_snapshot = LoanMarketSnapshotDTO(interest_rate=0.05)
    labor_snapshot = LaborMarketSnapshotDTO(avg_wage=0.0)
    market_signals = {}
    if 'goods_market' in market_data:
        for key, value in market_data['goods_market'].items():
            if '_current_sell_price' in key:
                item_id = key.replace('_current_sell_price', '')
                market_signals[item_id] = MarketSignalDTO(market_id='goods_market', item_id=item_id, best_bid={'amount': value * 0.9, 'currency': 'USD'}, best_ask={'amount': value, 'currency': 'USD'}, last_traded_price={'amount': value, 'currency': 'USD'}, last_trade_tick=market_data.get('time', 0), price_history_7d=[], volatility_7d=0.0, order_book_depth_buy=0, order_book_depth_sell=0, total_bid_quantity=0.0, total_ask_quantity=0.0, is_frozen=False)
    return MarketSnapshotDTO(tick=market_data.get('time', 0), market_signals=market_signals, housing=housing_snapshot, loan=loan_snapshot, labor=labor_snapshot, market_data=market_data)

def test_ai_creates_purchase_order(setup_test_environment, ai_engine_setup):
    """AI가 생존 욕구가 높을 때 'food' 구매 주문을 생성하는지 테스트합니다."""
    goods_data, markets = setup_test_environment
    ai_engine_registry, value_orientation = ai_engine_setup
    ai_decision_engine_instance = ai_engine_registry.get_engine(value_orientation)
    household_ai_instance = HouseholdAI(agent_id=str(2), ai_decision_engine=ai_decision_engine_instance)
    household_ai_instance.set_ai_decision_engine(ai_decision_engine_instance)
    household_decision_engine = AIDrivenHouseholdDecisionEngine(ai_engine=household_ai_instance, config_module=config)
    hh_config = create_config_dto(config, HouseholdConfigDTO)
    talent = Talent(base_learning_rate=0.1, max_potential={'strength': 100})
    household = create_household(config_dto=hh_config, id=2, value_orientation=value_orientation, initial_needs={'survival': 90.0, 'social': 20.0, 'improvement': 10.0, 'asset': 10.0}, name='Household_2', personality=Personality.MISER, assets=10000, engine=household_decision_engine, talent=talent, goods_data=goods_data)
    market_data = {'time': 1, 'goods_data': goods_data, 'goods_market': {'food_current_sell_price': 10.0, 'basic_food_current_sell_price': 10.0, 'luxury_food_current_sell_price': 50.0}}
    snapshot = create_mock_snapshot(market_data)
    input_dto = DecisionInputDTO(market_snapshot=snapshot, goods_data=goods_data, market_data=market_data, current_time=1)
    household.update_needs(1, market_data)
    orders, _ = household.make_decision(input_dto)
    assert orders is not None
    food_orders = [o for o in orders if 'food' in o.item_id and o.side == 'BUY']
    assert len(food_orders) > 0, 'Expected at least one food purchase order'
    purchase_order = food_orders[0]
    assert purchase_order.quantity > 0
    print('OK: AI successfully generated a purchase order for food.')

def test_ai_evaluates_consumption_options(setup_test_environment, ai_engine_setup):
    """
    AI가 여러 소비 옵션 중에서 욕구를 가장 잘 충족시키는(효용 대비 가격이 높은) 재화를 선택하는지 테스트합니다.
    여기서는 '사회적' 욕구가 높을 때 'luxury_food'를 선택하는지 확인합니다.
    """
    goods_data, markets = setup_test_environment
    ai_engine_registry, base_value_orientation = ai_engine_setup
    value_orientation = config.VALUE_ORIENTATION_NEEDS_AND_SOCIAL_STATUS
    ai_decision_engine_instance = ai_engine_registry.get_engine(value_orientation)
    household_ai_instance = HouseholdAI(agent_id=str(3), ai_decision_engine=ai_decision_engine_instance)
    household_ai_instance.set_ai_decision_engine(ai_decision_engine_instance)
    household_decision_engine = AIDrivenHouseholdDecisionEngine(ai_engine=household_ai_instance, config_module=config)
    hh_config = create_config_dto(config, HouseholdConfigDTO)
    talent = Talent(base_learning_rate=0.1, max_potential={'strength': 100})
    household = create_household(config_dto=hh_config, id=3, value_orientation=value_orientation, initial_needs={'survival': 10.0, 'social': 80.0, 'improvement': 10.0, 'asset': 10.0}, name='Household_3', personality=Personality.STATUS_SEEKER, assets=100000, engine=household_decision_engine, talent=talent, goods_data=goods_data)
    market_data = {'time': 1, 'goods_data': goods_data, 'goods_market': {'luxury_food_current_sell_price': 49.0, 'basic_food_current_sell_price': 10.0, 'food_current_sell_price': 10.0}}
    snapshot = create_mock_snapshot(market_data)
    input_dto = DecisionInputDTO(market_snapshot=snapshot, goods_data=goods_data, market_data=market_data, current_time=1)
    household.update_needs(1, market_data)
    orders, action_vector = household.make_decision(input_dto)
    assert orders is not None
    assert len(orders) > 0
    luxury_food_orders = [o for o in orders if o.item_id == 'luxury_food' and o.side == 'BUY']
    assert len(luxury_food_orders) > 0, 'Expected luxury_food purchase order'
    purchase_order = luxury_food_orders[0]
    assert purchase_order.quantity > 0
    assert purchase_order.quantity > 0
    print("OK: AI successfully evaluated consumption options and chose 'luxury_food'.")