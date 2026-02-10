import pytest
from simulation.decisions.firm.sales_manager import SalesManager

def test_pricing_logic(firm_dto, context_mock):
    from dataclasses import replace
    manager = SalesManager()

    new_prod = replace(firm_dto.production, inventory={"food": 100}, specialization="food")
    firm_dto = replace(firm_dto, production=new_prod)
    context_mock.state = firm_dto

    plan = manager.formulate_plan(context_mock, sales_aggressiveness=0.5)

    orders = plan.orders
    sell_orders = [o for o in orders if o.order_type == "SELL"]
    assert len(sell_orders) == 1
    assert sell_orders[0].quantity <= 100
    assert sell_orders[0].price > 0
