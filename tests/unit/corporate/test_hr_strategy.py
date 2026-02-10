import pytest
from dataclasses import replace
from simulation.decisions.firm.hr_strategy import HRStrategy

def test_hiring_logic(firm_dto, context_mock):
    manager = HRStrategy()

    # Update nested DTOs using replace
    new_prod = replace(firm_dto.production,
        production_target=100.0,
        inventory={"food": 80.0},
        productivity_factor=10.0
    )
    new_hr = replace(firm_dto.hr, employees=[])

    firm_dto = replace(firm_dto, production=new_prod, hr=new_hr)

    # Update context with the new DTO
    context_mock.state = firm_dto

    plan = manager.formulate_plan(context_mock, hiring_aggressiveness=0.5)

    hiring_orders = [o for o in plan.orders if o.order_type == "BUY" and o.item_id == "labor"]
    assert len(hiring_orders) > 0
    assert hiring_orders[0].price >= 10.0
