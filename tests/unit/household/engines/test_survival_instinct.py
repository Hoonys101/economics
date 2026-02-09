import pytest
from unittest.mock import MagicMock
from modules.household.engines.budget import BudgetEngine
from modules.household.engines.consumption import ConsumptionEngine
from modules.household.api import BudgetInputDTO, ConsumptionInputDTO, PrioritizedNeed, BudgetPlan
from modules.household.dtos import EconStateDTO, BioStateDTO
from simulation.dtos.config_dtos import HouseholdConfigDTO
from modules.system.api import MarketSnapshotDTO, DEFAULT_CURRENCY
from simulation.models import Order

# 1. BudgetEngine: Ensure 'survival' need overrides AI plan if funds are low
def test_budget_survival_priority():
    engine = BudgetEngine()

    econ_state = MagicMock(spec=EconStateDTO)
    econ_copy = MagicMock(spec=EconStateDTO)
    econ_state.copy.return_value = econ_copy

    # Low funds: 15.0
    econ_state.wallet = MagicMock()
    econ_state.wallet.get_balance.return_value = 15.0

    econ_copy.wallet = MagicMock()
    econ_copy.wallet.get_balance.return_value = 15.0
    # Add shadow wage etc to avoid other failures
    econ_copy.shadow_reservation_wage = 0.0
    econ_copy.is_employed = False
    econ_copy.expected_wage = 10.0
    econ_copy.market_wage_history = []
    econ_copy.is_homeless = False # Prevent housing logic crash

    prioritized_needs = [
        PrioritizedNeed(need_id="survival", urgency=100.0, deficit=50.0) # High urgency
    ]

    # Abstract Plan from AI
    abstract_order = Order(
        agent_id=1, side="BUY", item_id="entertainment", quantity=1.0, price_limit=10.0, market_id="goods"
    )
    abstract_plan = [abstract_order]

    market_snapshot = MagicMock(spec=MarketSnapshotDTO)
    market_snapshot.labor = MagicMock()
    market_snapshot.labor.avg_wage = 10.0
    # Food price 10.0
    market_snapshot.goods = {
        "food": MagicMock(avg_price=10.0),
        "basic_food": MagicMock(avg_price=10.0)
    }

    config = MagicMock(spec=HouseholdConfigDTO)
    config.household_min_wage_demand = 5.0
    config.survival_budget_allocation = 50.0
    config.default_food_price_estimate = 10.0

    input_dto = BudgetInputDTO(
        econ_state=econ_state,
        prioritized_needs=prioritized_needs,
        abstract_plan=abstract_plan,
        market_snapshot=market_snapshot,
        config=config,
        current_tick=1
    )

    output = engine.allocate_budget(input_dto)

    # Verification
    # 1. Food should be allocated (Needs Priority)
    assert output.budget_plan.allocations.get("food", 0.0) > 0.0

    # 2. AI Order (Entertainment) cost 10.0. Cash 15.0. Food took ~10.0 (or 50.0 capped).
    # Since only 15.0 total, and food takes priority, food gets 15.0.
    # Remaining for AI = 0.
    assert len(output.budget_plan.orders) == 0 # Entertainment dropped
    assert output.budget_plan.allocations["food"] == 15.0

# 2. ConsumptionEngine: Ensure food is bought if inventory low, even if AI didn't ask (Safety Net)
def test_consumption_survival_instinct():
    engine = ConsumptionEngine()

    econ_state = MagicMock(spec=EconStateDTO)
    econ_copy = MagicMock(spec=EconStateDTO)
    econ_state.copy.return_value = econ_copy

    # Inventory empty
    econ_copy.inventory = {"basic_food": 0.0}
    econ_copy.durable_assets = []
    # Mock portfolio for owner_id
    econ_copy.portfolio = MagicMock()
    econ_copy.portfolio.owner_id = 1
    # Mock wallet for panic check
    econ_copy.wallet = MagicMock()
    econ_copy.wallet.get_balance.return_value = 1000.0

    # High survival need
    bio_state = BioStateDTO(id=1, age=20.0, gender="M", generation=0, is_active=True, needs={"survival": 100.0})

    # Budget allocated for food (by BudgetEngine)
    budget_plan = BudgetPlan(allocations={"food": 20.0}, discretionary_spending=0.0, orders=[])

    market_snapshot = MagicMock(spec=MarketSnapshotDTO)
    # Food price
    market_snapshot.goods = {
        "basic_food": MagicMock(avg_price=10.0)
    }

    config = MagicMock(spec=HouseholdConfigDTO)

    input_dto = ConsumptionInputDTO(
        econ_state=econ_state,
        bio_state=bio_state,
        budget_plan=budget_plan,
        market_snapshot=market_snapshot,
        config=config,
        current_tick=1
    )

    output = engine.generate_orders(input_dto)

    # Should generate a BUY order for food
    food_orders = [o for o in output.orders if o.item_id == "basic_food" and o.side == "BUY"]
    assert len(food_orders) > 0
    # Quantity: 20.0 alloc / 10.0 price = 2.0
    assert food_orders[0].quantity == 2.0
