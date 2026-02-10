import pytest
from simulation.decisions.firm.production_strategy import ProductionStrategy

def test_rd_logic(firm_dto, context_mock):
    from dataclasses import replace
    manager = ProductionStrategy()

    new_fin = replace(firm_dto.finance, balance=10000.0, revenue_this_turn=1000.0)
    firm_dto = replace(firm_dto, finance=new_fin)
    context_mock.state = firm_dto

    expected_budget = 1000.0 * 0.2 # 200

    plan = manager.formulate_plan(context_mock, capital_aggressiveness=0.0, rd_aggressiveness=1.0, guidance={})

    rd_orders = [o for o in plan.orders if o.order_type == "INVEST_RD"]
    assert len(rd_orders) == 1
    assert rd_orders[0].quantity == expected_budget
    assert rd_orders[0].market_id == "internal"

def test_automation_investment(firm_dto, context_mock):
    from dataclasses import replace
    # Update config DTO
    context_mock.config.automation_cost_per_pct = 10.0

    manager = ProductionStrategy()

    # High wages so automation saves money (for guidance simulation, but here guidance is passed in)
    # firm_dto is frozen, so we must replace hr state for employees_data
    # employees_data is in HRStateDTO
    new_hr = replace(firm_dto.hr, employees_data={
        1: {"wage": 2000.0, "skill": 1.0, "id": 1, "age": 20, "education_level": 1}
    })

    new_fin = replace(firm_dto.finance, revenue_this_turn=5000.0, balance=50000.0)

    firm_dto = replace(firm_dto, hr=new_hr, finance=new_fin)
    context_mock.state = firm_dto

    # Provide guidance that requests automation
    guidance = {"target_automation": 0.5} # Higher than current 0.0

    plan = manager.formulate_plan(context_mock, capital_aggressiveness=1.0, rd_aggressiveness=0.0, guidance=guidance)

    auto_orders = [o for o in plan.orders if o.order_type == "INVEST_AUTOMATION"]
    assert len(auto_orders) > 0
    assert auto_orders[0].quantity > 0
