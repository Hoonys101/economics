import pytest
from simulation.decisions.firm.sales_manager import SalesManager

def test_pricing_logic(firm_dto, context_mock):
    manager = SalesManager()

    firm_dto.inventory = {"food": 100}
    firm_dto.specialization = "food"

    plan = manager.formulate_plan(context_mock, sales_aggressiveness=0.5)

    orders = plan.orders
    sell_orders = [o for o in orders if o.order_type == "SELL"]
    assert len(sell_orders) == 1
    assert sell_orders[0].quantity <= 100
    assert sell_orders[0].price > 0
