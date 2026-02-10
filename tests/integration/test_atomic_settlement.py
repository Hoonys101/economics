import pytest
from unittest.mock import MagicMock
from simulation.systems.settlement_system import SettlementSystem

class MockAgent:
    def __init__(self, id, assets=100.0):
        self.id = id
        self.assets = assets

    def deposit(self, amount, currency="USD"):
        if amount < 0: raise ValueError("Negative deposit")
        self.assets += amount

    def withdraw(self, amount, currency="USD"):
        if amount < 0: raise ValueError("Negative withdraw")
        # SettlementSystem checks assets property manually before calling withdraw,
        # but pure withdraw should also work.
        if self.assets < amount:
             # In simulation context, withdraw might raise InsufficientFundsError
             # but here we just decrement or let it go negative if not checked strictly by method.
             pass
        self.assets -= amount

def test_settle_atomic_success():
    settlement = SettlementSystem()
    debit_agent = MockAgent(1, 100.0)
    credit_agent1 = MockAgent(2, 0.0)
    credit_agent2 = MockAgent(3, 0.0)

    credits = [
        (credit_agent1, 30.0, "c1"),
        (credit_agent2, 20.0, "c2")
    ]

    success = settlement.settle_atomic(debit_agent, credits, tick=1)

    assert success is True
    assert debit_agent.assets == 50.0
    assert credit_agent1.assets == 30.0
    assert credit_agent2.assets == 20.0

def test_settle_atomic_rollback():
    settlement = SettlementSystem()
    debit_agent = MockAgent(1, 100.0)
    credit_agent1 = MockAgent(2, 0.0)
    credit_agent2 = MockAgent(3, 0.0)

    # Mock credit_agent2 to fail on deposit
    credit_agent2.deposit = MagicMock(side_effect=Exception("Bank Frozen"))

    credits = [
        (credit_agent1, 30.0, "c1"),
        (credit_agent2, 20.0, "c2")
    ]

    success = settlement.settle_atomic(debit_agent, credits, tick=1)

    assert success is False
    assert debit_agent.assets == 100.0 # Full refund (100 - 50 + 50)
    assert credit_agent1.assets == 0.0 # Rolled back (0 + 30 - 30)

    # Verify that credit_agent2.deposit was called
    credit_agent2.deposit.assert_called_once()
