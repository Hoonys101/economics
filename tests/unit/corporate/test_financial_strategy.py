import pytest
from simulation.decisions.firm.financial_strategy import FinancialStrategy

def test_dividend_logic(firm_dto, context_mock):
    manager = FinancialStrategy()

    plan = manager.formulate_plan(context_mock, dividend_aggressiveness=1.0, debt_aggressiveness=0.0)

    div_orders = [o for o in plan.orders if o.order_type == "SET_DIVIDEND"]
    assert len(div_orders) == 1
    assert div_orders[0].quantity == 0.5

def test_debt_logic_borrow(firm_dto, context_mock):
    from dataclasses import replace
    manager = FinancialStrategy()

    new_fin = replace(firm_dto.finance, balance=1000.0)
    firm_dto = replace(firm_dto, finance=new_fin)
    context_mock.state = firm_dto

    context_mock.market_data["debt_data"] = {firm_dto.id: {"total_principal": 0.0}}

    plan = manager.formulate_plan(context_mock, dividend_aggressiveness=0.0, debt_aggressiveness=0.5)

    loan_reqs = [o for o in plan.orders if o.order_type == "LOAN_REQUEST"]
    assert len(loan_reqs) > 0
    assert loan_reqs[0].quantity > 0
