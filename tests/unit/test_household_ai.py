import os
import sys
import json
import pytest
from tests.utils.factories import create_firm_config_dto, create_household_config_dto
from unittest.mock import Mock

# Add project root to sys.path to allow imports from other modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
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
from simulation.dtos.config_dtos import HouseholdConfigDTO
from simulation.ai.enums import Tactic
from simulation.dtos.api import DecisionInputDTO

@pytest.fixture
def setup_test_environment():
    """Fixture to set up the test environment."""
    goods_json_path = os.path.join(project_root, "data", "goods.json")
    try:
        with open(goods_json_path, "r", encoding="utf-8") as f:
            goods_data = json.load(f)
    except FileNotFoundError:
        pytest.fail(f"Error: {goods_json_path} not found.")

    markets = {
        "goods_market": OrderBookMarket("goods_market"),
        "labor_market": OrderBookMarket("labor_market"),
        "loan_market": Mock(spec=Market),
    }
    
    # Pre-populate goods market with some offers for testing
    goods_market = markets["goods_market"]
    goods_market.place_order(Order(agent_id=99, side="SELL", item_id="basic_food", quantity=100, price_limit=10.0, market_id="goods_market"), 0)
    goods_market.place_order(Order(agent_id=98, side="SELL", item_id="luxury_food", quantity=50, price_limit=50.0, market_id="goods_market"), 0)
    
    return goods_data, markets

@pytest.fixture
def ai_engine_setup():
    """Fixture for setting up AI engine components."""
    value_orientation = config.VALUE_ORIENTATION_WEALTH_AND_NEEDS
    action_proposal_engine = ActionProposalEngine(config_module=config, n_action_samples=10)
    state_builder = StateBuilder()
    ai_engine_registry = AIEngineRegistry(
        action_proposal_engine=action_proposal_engine, state_builder=state_builder
    )
    return ai_engine_registry, value_orientation

def test_ai_creates_purchase_order(setup_test_environment, ai_engine_setup):
    """AI가 생존 욕구가 높을 때 'food' 구매 주문을 생성하는지 테스트합니다."""
    goods_data, markets = setup_test_environment
    ai_engine_registry, value_orientation = ai_engine_setup

    ai_decision_engine_instance = ai_engine_registry.get_engine(value_orientation)
    household_ai_instance = HouseholdAI(agent_id=str(2), ai_decision_engine=ai_decision_engine_instance)
    household_ai_instance.set_ai_decision_engine(ai_decision_engine_instance)
    household_decision_engine = AIDrivenHouseholdDecisionEngine(
        ai_engine=household_ai_instance, config_module=config
    )

    hh_config = create_config_dto(config, HouseholdConfigDTO)
    talent = Talent(base_learning_rate=0.1, max_potential={"strength": 100})
    household = Household(
        id=2,
        talent=talent,
        goods_data=goods_data,
        initial_assets=100.0,
        initial_needs={"survival": 80.0, "social": 20.0, "improvement": 10.0, "asset": 10.0},
        value_orientation=value_orientation,
        decision_engine=household_decision_engine,
        personality=Personality.MISER,
        config_dto=hh_config,
    )

    market_data = {
        "time": 1,
        "goods_data": goods_data,
        "goods_market": {
             "food_current_sell_price": 10.0,
             "basic_food_current_sell_price": 10.0,
             "luxury_food_current_sell_price": 50.0,
        }
    }

    input_dto = DecisionInputDTO(
        markets=markets,
        goods_data=goods_data,
        market_data=market_data,
        current_time=1
    )
    orders, _ = household.make_decision(input_dto)

    assert orders is not None
    # Check if any order is for food
    food_orders = [o for o in orders if "food" in o.item_id and o.side == "BUY"]
    assert len(food_orders) > 0, "Expected at least one food purchase order"
    
    purchase_order = food_orders[0]
    assert purchase_order.quantity > 0
    
    print("OK: AI successfully generated a purchase order for food.")

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
    household_decision_engine = AIDrivenHouseholdDecisionEngine(
        ai_engine=household_ai_instance, config_module=config
    )

    hh_config = create_config_dto(config, HouseholdConfigDTO)
    talent = Talent(base_learning_rate=0.1, max_potential={"strength": 100})
    household = Household(
        id=3,
        talent=talent,
        goods_data=goods_data,
        initial_assets=1000.0,
        initial_needs={"survival": 10.0, "social": 80.0, "improvement": 10.0, "asset": 10.0},
        value_orientation=value_orientation,
        decision_engine=household_decision_engine,
        personality=Personality.STATUS_SEEKER,
        config_dto=hh_config,
    )

    market_data = {
        "time": 1,
        "goods_data": goods_data,
        "goods_market": {
             "luxury_food_current_sell_price": 50.0,
             "basic_food_current_sell_price": 10.0,
             "food_current_sell_price": 10.0,
        }
    }

    input_dto = DecisionInputDTO(
        markets=markets,
        goods_data=goods_data,
        market_data=market_data,
        current_time=1
    )
    orders, action_vector = household.make_decision(input_dto)

    assert orders is not None
    assert len(orders) > 0
    
    # Check if luxury_food is bought
    luxury_food_orders = [o for o in orders if o.item_id == "luxury_food" and o.side == "BUY"]
    assert len(luxury_food_orders) > 0, "Expected luxury_food purchase order"

    purchase_order = luxury_food_orders[0]
    assert purchase_order.quantity > 0
    assert purchase_order.quantity > 0
    
    print("OK: AI successfully evaluated consumption options and chose 'luxury_food'.")
