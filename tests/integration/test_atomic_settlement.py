import pytest
from unittest.mock import MagicMock
from simulation.systems.settlement_system import SettlementSystem
from modules.system.api import DEFAULT_CURRENCY

class MockAgent:
    def __init__(self, id, assets=10000):
        self.id = id
        self.assets = int(assets)

    def deposit(self, amount: int, currency=DEFAULT_CURRENCY):
        if amount < 0: raise ValueError("Negative deposit")
        self.assets += amount

    def withdraw(self, amount: int, currency=DEFAULT_CURRENCY):
        if amount < 0: raise ValueError("Negative withdraw")
        # SettlementSystem checks assets property manually before calling withdraw,
        # but pure withdraw should also work.
        if self.assets < amount:
             # In simulation context, withdraw might raise InsufficientFundsError
             # but here we just decrement or let it go negative if not checked strictly by method.
             pass
        self.assets -= amount

    def get_balance(self, currency=DEFAULT_CURRENCY) -> int:
        return self.assets

def test_settle_atomic_success():
    settlement = SettlementSystem()
    debit_agent = MockAgent(1, 10000) # $100.00
    credit_agent1 = MockAgent(2, 0)
    credit_agent2 = MockAgent(3, 0)

    credits = [
        (credit_agent1, 3000, "c1"), # $30.00
        (credit_agent2, 2000, "c2")  # $20.00
    ]

    success = settlement.settle_atomic(debit_agent, credits, tick=1)

    assert success is True
    assert debit_agent.assets == 5000
    assert credit_agent1.assets == 3000
    assert credit_agent2.assets == 2000

def test_settle_atomic_rollback():
    settlement = SettlementSystem()
    debit_agent = MockAgent(1, 10000)
    credit_agent1 = MockAgent(2, 0)
    credit_agent2 = MockAgent(3, 0)

    # Mock credit_agent2 to fail on deposit
    credit_agent2.deposit = MagicMock(side_effect=Exception("Bank Frozen"))

    credits = [
        (credit_agent1, 3000, "c1"),
        (credit_agent2, 2000, "c2")
    ]

    success = settlement.settle_atomic(debit_agent, credits, tick=1)

    assert success is False
    assert debit_agent.assets == 10000 # Full refund
    assert credit_agent1.assets == 0 # Rolled back

    # Verify that credit_agent2.deposit was called
    credit_agent2.deposit.assert_called_once()
