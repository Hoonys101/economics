import pytest
from simulation.decisions.firm.hr_manager import HRManager

def test_hiring_logic(firm_dto, context_mock):
    manager = HRManager()
    firm_dto.production_target = 100
    firm_dto.inventory["food"] = 80 # Gap 20
    firm_dto.productivity_factor = 10.0 # Need 2 workers (approx)

    # Adjust mock to return empty list of employees so we hire
    firm_dto.employees = []

    plan = manager.formulate_plan(context_mock, hiring_aggressiveness=0.5)

    hiring_orders = [o for o in plan.orders if o.order_type == "BUY" and o.item_id == "labor"]
    assert len(hiring_orders) > 0
    assert hiring_orders[0].price >= 10.0
