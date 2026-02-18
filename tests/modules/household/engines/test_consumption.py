import pytest
from unittest.mock import MagicMock
from modules.household.engines.consumption_engine import ConsumptionEngine
from modules.household.api import ConsumptionInputDTO, BudgetPlan
from modules.household.dtos import EconStateDTO, BioStateDTO
from simulation.models import Order
from modules.simulation.dtos.api import HouseholdConfigDTO

@pytest.fixture
def consumption_engine():
    return ConsumptionEngine()

@pytest.fixture
def input_dto():
    econ_state = MagicMock(spec=EconStateDTO)
    econ_state.wallet = MagicMock()
    econ_state.inventory = {'basic_food': 0.0}
    econ_state.wallet.get_balance.return_value = 100.0
    econ_state.copy.return_value = econ_state
    econ_state.durable_assets = []
    bio_state = MagicMock(spec=BioStateDTO)
    bio_state.needs = {'survival': 50.0}
    bio_state.copy.return_value = bio_state
    order = Order(agent_id=1, side='BUY', item_id='basic_food', quantity=5.0, price_pennies=int(11.0 * 100), price_limit=11.0, market_id='goods_market')
    budget_plan = BudgetPlan(allocations={'food': 50.0}, discretionary_spending=50.0, orders=[order])
    config = MagicMock(spec=HouseholdConfigDTO)
    config.panic_selling_asset_threshold = 0.0
    return ConsumptionInputDTO(econ_state=econ_state, bio_state=bio_state, budget_plan=budget_plan, market_snapshot=MagicMock(), config=config, current_tick=1, stress_scenario_config=None)

def test_generate_orders_uses_budget_orders(consumption_engine, input_dto):
    output = consumption_engine.generate_orders(input_dto)
    assert len(output.orders) == 1
    assert output.orders[0].item_id == 'basic_food'
    assert output.orders[0].quantity == 5.0