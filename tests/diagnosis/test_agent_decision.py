import pytest
from unittest.mock import MagicMock
from simulation.models import Order
from simulation.core_agents import Household
from simulation.firms import Firm


def test_household_makes_decision(simple_household):
    """Spec 0: 에이전트가 주문을 생성하는지 검증 (Household)"""
    # Arrange
    # Mock the decision engine to return a specific action
    expected_order = Order(
        agent_id=simple_household.id,
        order_type="BUY",
        item_id="basic_food",
        quantity=1.0,
        price=10.0,
        market_id="basic_food",
    )
    # make_decisions returns (orders, tactic)
    simple_household.decision_engine.make_decisions = MagicMock(
        return_value=([expected_order], None)
    )

    # Act
    orders, tactic = simple_household.make_decision(
        markets={}, goods_data=[], market_data={}, current_time=1
    )

    # Assert
    assert len(orders) == 1
    assert orders[0].order_type == "BUY"
    assert orders[0].item_id == "basic_food"
    assert orders[0].price == 10.0


def test_firm_makes_decision(simple_firm):
    """Spec 0: 에이전트가 주문을 생성하는지 검증 (Firm)"""
    # Arrange
    expected_order = Order(
        agent_id=simple_firm.id,
        order_type="SELL",
        item_id="basic_food",
        quantity=5.0,
        price=12.0,
        market_id="basic_food",
    )
    # make_decisions returns (orders, tactic)
    simple_firm.decision_engine.make_decisions = MagicMock(
        return_value=([expected_order], None)
    )

    # Act
    # Firm likely has make_decision too? Checking Firm class would be good,
    # but assuming consistency with BaseAgent.
    orders, tactic = simple_firm.make_decision(
        markets={}, goods_data=[], market_data={}, current_time=1
    )

    # Assert
    assert len(orders) == 1
    assert orders[0].order_type == "SELL"
    assert orders[0].item_id == "basic_food"
