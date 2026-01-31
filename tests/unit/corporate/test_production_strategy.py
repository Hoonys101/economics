import pytest
from simulation.decisions.firm.production_strategy import ProductionStrategy

def test_rd_logic(firm_dto, context_mock):
    manager = ProductionStrategy()

    firm_dto.assets = 10000.0
    firm_dto.revenue_this_turn = 1000.0
    expected_budget = 1000.0 * 0.2 # 200

    plan = manager.formulate_plan(context_mock, capital_aggressiveness=0.0, rd_aggressiveness=1.0, guidance={})

    rd_orders = [o for o in plan.orders if o.order_type == "INVEST_RD"]
    assert len(rd_orders) == 1
    assert rd_orders[0].quantity == expected_budget
    assert rd_orders[0].market_id == "internal"

def test_automation_investment(firm_dto, context_mock):
    # Update config DTO
    context_mock.config.automation_cost_per_pct = 10.0

    manager = ProductionStrategy()

    # High wages so automation saves money (for guidance simulation, but here guidance is passed in)
    firm_dto.employees_data = {
        1: {"wage": 2000.0, "skill": 1.0, "id": 1, "age": 20, "education_level": 1}
    }
    firm_dto.revenue_this_turn = 5000.0
    firm_dto.assets = 50000.0 # Plenty of cash

    # Provide guidance that requests automation
    guidance = {"target_automation": 0.5} # Higher than current 0.0

    plan = manager.formulate_plan(context_mock, capital_aggressiveness=1.0, rd_aggressiveness=0.0, guidance=guidance)

    auto_orders = [o for o in plan.orders if o.order_type == "INVEST_AUTOMATION"]
    assert len(auto_orders) > 0
    assert auto_orders[0].quantity > 0
