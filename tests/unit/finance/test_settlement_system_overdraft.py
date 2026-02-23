import pytest
from unittest.mock import MagicMock
from simulation.systems.settlement_system import SettlementSystem
from modules.finance.api import IFinancialAgent, IFinancialEntity
from modules.system.api import DEFAULT_CURRENCY, ISystemFinancialAgent

class MockNormalAgent(IFinancialAgent):
    def __init__(self, id, balance):
        self.id = id
        self._balance_pennies = balance

    @property
    def balance_pennies(self):
        return self._balance_pennies

    @balance_pennies.setter
    def balance_pennies(self, value):
        self._balance_pennies = value

    def deposit(self, amount, currency=DEFAULT_CURRENCY):
        self.balance_pennies += amount

    def withdraw(self, amount, currency=DEFAULT_CURRENCY):
        self.balance_pennies -= amount

    def get_balance(self, currency=DEFAULT_CURRENCY):
        return self.balance_pennies

    def _deposit(self, amount, currency=DEFAULT_CURRENCY):
        self.deposit(amount, currency)

    def _withdraw(self, amount, currency=DEFAULT_CURRENCY):
        self.withdraw(amount, currency)

    def get_all_balances(self):
        return {DEFAULT_CURRENCY: self.balance_pennies}

    @property
    def total_wealth(self):
        return self.balance_pennies

    def get_liquid_assets(self, currency="USD"):
        return self.balance_pennies / 100.0

    def get_total_debt(self):
        return 0.0

class MockSystemAgent(MockNormalAgent, ISystemFinancialAgent):
    def is_system_agent(self) -> bool:
        return True

class TestSettlementSystemOverdraft:

    @pytest.fixture
    def settlement_system(self):
        return SettlementSystem()

    def test_normal_agent_cannot_overdraft(self, settlement_system):
        agent_a = MockNormalAgent(1, 100)
        agent_b = MockNormalAgent(2, 0)

        # Try to transfer 200 from A to B
        result = settlement_system.transfer(agent_a, agent_b, 200, "test")

        assert result is None
        assert agent_a.balance_pennies == 100
        assert agent_b.balance_pennies == 0

    def test_system_agent_can_overdraft(self, settlement_system):
        pm = MockSystemAgent(4, 0)
        agent_b = MockNormalAgent(2, 0)

        # Try to transfer 200 from PM to B
        result = settlement_system.transfer(pm, agent_b, 200, "bailout")

        assert result is not None
        assert pm.balance_pennies == -200
        assert agent_b.balance_pennies == 200
