import pytest
from unittest.mock import MagicMock
from typing import List, Any, Dict
from simulation.systems.settlement_system import SettlementSystem
from modules.system.api import DEFAULT_CURRENCY, IAgentRegistry
from modules.finance.api import IFinancialEntity, IFinancialAgent, InsufficientFundsError

class MockAgent: # Implements IFinancialEntity and IFinancialAgent
    def __init__(self, id, assets=10000):
        self.id = id
        self._assets = int(assets)

    @property
    def balance_pennies(self) -> int:
        return self._assets

    def deposit(self, amount: int, currency=DEFAULT_CURRENCY):
        self._deposit(amount, currency)

    def withdraw(self, amount: int, currency=DEFAULT_CURRENCY):
        self._withdraw(amount, currency)

    def _deposit(self, amount: int, currency=DEFAULT_CURRENCY):
        if amount < 0: raise ValueError("Negative deposit")
        self._assets += amount

    def _withdraw(self, amount: int, currency=DEFAULT_CURRENCY):
        if amount < 0: raise ValueError("Negative withdraw")
        if self._assets < amount:
             raise InsufficientFundsError(f"Insufficient Funds: {self._assets} < {amount}")
        self._assets -= amount

    def get_balance(self, currency=DEFAULT_CURRENCY) -> int:
        return self._assets

    def get_all_balances(self) -> Dict[str, int]:
        return {DEFAULT_CURRENCY: self._assets}

    @property
    def total_wealth(self) -> int:
        return self._assets

    def get_liquid_assets(self, currency="USD") -> float:
        return float(self._assets)

    def get_total_debt(self) -> float:
        return 0.0

class MockRegistry:
    def __init__(self, agents: List[Any]):
        self.agents = {agent.id: agent for agent in agents}

    def get_agent(self, agent_id: Any) -> Any:
        return self.agents.get(agent_id)

    def get_all_financial_agents(self) -> List[Any]:
        return list(self.agents.values())

    def set_state(self, state: Any) -> None:
        pass

def test_settle_atomic_success():
    debit_agent = MockAgent(1, 10000) # $100.00
    credit_agent1 = MockAgent(2, 0)
    credit_agent2 = MockAgent(3, 0)

    registry = MockRegistry([debit_agent, credit_agent1, credit_agent2])
    settlement = SettlementSystem()
    settlement.agent_registry = registry

    credits = [
        (credit_agent1, 3000, "c1"), # $30.00
        (credit_agent2, 2000, "c2")  # $20.00
    ]

    success = settlement.settle_atomic(debit_agent, credits, tick=1)

    assert success is True
    # SSoT Verification
    assert settlement.get_balance(debit_agent.id) == 5000
    assert settlement.get_balance(credit_agent1.id) == 3000
    assert settlement.get_balance(credit_agent2.id) == 2000

def test_settle_atomic_rollback():
    debit_agent = MockAgent(1, 10000)
    credit_agent1 = MockAgent(2, 0)
    credit_agent2 = MockAgent(3, 0)

    # Mock credit_agent2 to fail on deposit
    # We patch _deposit to simulate failure, as settle_atomic calls _deposit or deposit
    credit_agent2._deposit = MagicMock(side_effect=Exception("Bank Frozen"))
    credit_agent2.deposit = credit_agent2._deposit # Ensure protocol method also fails

    registry = MockRegistry([debit_agent, credit_agent1, credit_agent2])
    settlement = SettlementSystem()
    settlement.agent_registry = registry

    credits = [
        (credit_agent1, 3000, "c1"),
        (credit_agent2, 2000, "c2")
    ]

    success = settlement.settle_atomic(debit_agent, credits, tick=1)

    assert success is False
    # SSoT Verification: Full Rollback
    assert settlement.get_balance(debit_agent.id) == 10000
    assert settlement.get_balance(credit_agent1.id) == 0

    # Verify that credit_agent2.deposit was called
    credit_agent2._deposit.assert_called_once()
