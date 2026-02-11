import pytest
from unittest.mock import MagicMock, Mock
from modules.household.engines.budget import BudgetEngine
from modules.household.api import BudgetInputDTO, PrioritizedNeed
from modules.household.dtos import EconStateDTO
from simulation.dtos.config_dtos import HouseholdConfigDTO
from modules.system.api import DEFAULT_CURRENCY
from simulation.models import Order

@pytest.fixture
def budget_engine():
    return BudgetEngine()

@pytest.fixture
def mock_config():
    config = MagicMock(spec=HouseholdConfigDTO)
    config.default_food_price_estimate = 10.0
    config.survival_budget_allocation = 50.0
    config.household_min_wage_demand = 10.0
    return config

@pytest.fixture
def econ_state():
    wallet = MagicMock()
    wallet.get_balance.return_value = 10000 # 100.00
    wallet.owner_id = 1

    state = MagicMock(spec=EconStateDTO)
    state.wallet = wallet
    state.is_employed = False
    state.shadow_reservation_wage_pennies = 1000
    state.market_wage_history = []
    state.is_homeless = True
    state.current_wage_pennies = 0
    state.residing_property_id = None
    state.copy.return_value = state
    return state

def test_allocate_budget_creates_orders_for_needs(budget_engine, econ_state, mock_config):
    prioritized_needs = [
        PrioritizedNeed(need_id="survival", urgency=1.0, deficit=50.0)
    ]
    abstract_plan = []
    market_snapshot = MagicMock()
    # Mock goods market
    market_snapshot.goods = {"basic_food": MagicMock(avg_price=10.0)}
    market_snapshot.labor.avg_wage = 15.0

    input_dto = BudgetInputDTO(
        econ_state=econ_state,
        prioritized_needs=prioritized_needs,
        abstract_plan=abstract_plan,
        market_snapshot=market_snapshot,
        config=mock_config,
        current_tick=1
    )

    output = budget_engine.allocate_budget(input_dto)

    assert "food" in output.budget_plan.allocations
    assert output.budget_plan.allocations["food"] == 5000 # 50.00

    # Verify Order creation
    assert len(output.budget_plan.orders) == 1
    order = output.budget_plan.orders[0]
    assert order.item_id == "basic_food"
    assert order.side == "BUY"
    assert order.quantity == 5.0 # 50.0 / 10.0
