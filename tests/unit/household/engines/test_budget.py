import pytest
from unittest.mock import MagicMock
from modules.household.engines.budget import BudgetEngine
from modules.household.api import BudgetInputDTO, PrioritizedNeed
from modules.household.dtos import EconStateDTO
from simulation.dtos.config_dtos import HouseholdConfigDTO
from modules.system.api import MarketSnapshotDTO, DEFAULT_CURRENCY

def test_budget_allocation():
    engine = BudgetEngine()

    econ_state = MagicMock(spec=EconStateDTO)
    econ_state.wallet = MagicMock()
    econ_state.wallet.get_balance.return_value = 100.0

    econ_copy = MagicMock(spec=EconStateDTO)
    econ_copy.wallet = MagicMock()
    econ_copy.wallet.get_balance.return_value = 100.0
    econ_copy.shadow_reservation_wage = 0.0
    econ_copy.is_employed = False
    econ_copy.expected_wage = 10.0
    econ_copy.market_wage_history = [] # Use list instead of deque for test simplicity
    econ_copy.is_homeless = False

    econ_state.copy.return_value = econ_copy

    prioritized_needs = [
        PrioritizedNeed(need_id="survival", urgency=10.0, deficit=10.0)
    ]

    abstract_plan = []

    market_snapshot = MagicMock(spec=MarketSnapshotDTO)
    market_snapshot.goods = {"food": MagicMock(avg_price=10.0)}
    market_snapshot.labor = MagicMock(avg_wage=10.0)

    config = MagicMock(spec=HouseholdConfigDTO)
    config.household_min_wage_demand = 5.0
    # Set new config values to avoid defaults (though defaults exist in logic, explicit is better for test intent)
    config.default_food_price_estimate = 10.0
    config.survival_budget_allocation = 50.0

    input_dto = BudgetInputDTO(
        econ_state=econ_state,
        prioritized_needs=prioritized_needs,
        abstract_plan=abstract_plan,
        market_snapshot=market_snapshot,
        config=config,
        current_tick=1
    )

    output = engine.allocate_budget(input_dto)

    # 50.0 allocated to food (default amount in engine placeholder)
    assert output.budget_plan.allocations["food"] == 50.0
    assert output.budget_plan.discretionary_spending == 50.0
