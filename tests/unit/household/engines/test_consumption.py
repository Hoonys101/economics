import pytest
from unittest.mock import MagicMock
from modules.household.engines.consumption import ConsumptionEngine
from modules.household.api import ConsumptionInputDTO, BudgetPlan
from modules.household.dtos import EconStateDTO, BioStateDTO
from simulation.dtos.config_dtos import HouseholdConfigDTO
from modules.system.api import MarketSnapshotDTO, DEFAULT_CURRENCY

def test_consumption_execution():
    engine = ConsumptionEngine()

    econ_state = MagicMock(spec=EconStateDTO)

    econ_copy = MagicMock(spec=EconStateDTO)
    econ_copy.inventory = {"basic_food": 2.0}
    econ_copy.durable_assets = []
    econ_copy.wallet = MagicMock()
    econ_copy.wallet.get_balance.return_value = 1000.0

    econ_state.copy.return_value = econ_copy

    bio_state = BioStateDTO(id=1, age=20.0, gender="M", generation=0, is_active=True, needs={"survival": 100.0})

    budget_plan = BudgetPlan(allocations={"food": 50.0}, discretionary_spending=0.0)

    market_snapshot = MagicMock(spec=MarketSnapshotDTO)
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

    # Check inventory reduction (consumed 1 unit)
    assert output.econ_state.inventory["basic_food"] == 1.0
    # Check needs reduction
    assert output.bio_state.needs["survival"] == 80.0
