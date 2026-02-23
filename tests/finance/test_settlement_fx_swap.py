import pytest
from unittest.mock import MagicMock
from typing import Dict, Any
from modules.finance.api import IFinancialAgent, FXMatchDTO
from simulation.systems.settlement_system import SettlementSystem
from modules.system.api import IAgentRegistry, DEFAULT_CURRENCY

# Mock Agent Class that implements IFinancialAgent and ITransactionParticipant
class MockFinancialAgent:
    def __init__(self, agent_id: int, balances: Dict[str, int]):
        self.id = agent_id
        self._balances = balances
        self.allows_overdraft = False

    def get_balance(self, currency: str = "USD") -> int:
        return self._balances.get(currency, 0)

    def deposit(self, amount: int, currency: str = "USD", memo: str = ""):
        self._balances[currency] = self._balances.get(currency, 0) + amount

    def withdraw(self, amount: int, currency: str = "USD", memo: str = ""):
        current = self._balances.get(currency, 0)
        if current < amount and not self.allows_overdraft:
            raise Exception("Insufficient funds")
        self._balances[currency] = current - amount

    @property
    def balance_pennies(self) -> int:
        return self._balances.get(DEFAULT_CURRENCY, 0)

    # Implement protocol requirements for IFinancialAgent
    def _deposit(self, amount: int, currency: str = "USD") -> None:
        self.deposit(amount, currency)

    def _withdraw(self, amount: int, currency: str = "USD") -> None:
        self.withdraw(amount, currency)

    def get_liquid_assets(self, currency: str = "USD") -> float:
        return float(self.get_balance(currency)) / 100.0

    def get_total_debt(self) -> float:
        return 0.0

    def get_all_balances(self) -> Dict[str, int]:
        return self._balances.copy()

    @property
    def total_wealth(self) -> int:
        return sum(self._balances.values())

@pytest.fixture
def settlement_system():
    registry = MagicMock(spec=IAgentRegistry)
    system = SettlementSystem(agent_registry=registry)
    return system, registry

def test_execute_swap_success(settlement_system):
    system, registry = settlement_system

    # Setup Agents
    agent_a = MockFinancialAgent(101, {"USD": 1000, "EUR": 0})
    agent_b = MockFinancialAgent(102, {"USD": 0, "EUR": 1000})

    # Configure Registry to return these mocks
    # Note: get_agent uses loose typing in code, expecting integer or string ID
    def get_agent_side_effect(agent_id: Any):
        aid = int(agent_id)
        return {101: agent_a, 102: agent_b}.get(aid)

    registry.get_agent.side_effect = get_agent_side_effect

    # Define Match
    match = FXMatchDTO(
        party_a_id=101,
        party_b_id=102,
        amount_a_pennies=500,
        currency_a="USD",
        amount_b_pennies=400,
        currency_b="EUR",
        match_tick=1,
        rate_a_to_b=0.8
    )

    # Execute
    tx = system.execute_swap(match)

    # Verify
    assert tx is not None
    assert tx.transaction_type == "FX_SWAP"

    # Balances
    assert agent_a.get_balance("USD") == 500  # 1000 - 500
    assert agent_a.get_balance("EUR") == 400  # 0 + 400
    assert agent_b.get_balance("USD") == 500  # 0 + 500
    assert agent_b.get_balance("EUR") == 600  # 1000 - 400

def test_execute_swap_insufficient_funds_rollback(settlement_system):
    system, registry = settlement_system

    # Setup Agents: Agent A has enough USD, Agent B does NOT have enough EUR
    agent_a = MockFinancialAgent(101, {"USD": 1000, "EUR": 0})
    agent_b = MockFinancialAgent(102, {"USD": 0, "EUR": 100}) # Only 100 EUR, needs 400

    def get_agent_side_effect(agent_id: Any):
        aid = int(agent_id)
        return {101: agent_a, 102: agent_b}.get(aid)

    registry.get_agent.side_effect = get_agent_side_effect

    match = FXMatchDTO(
        party_a_id=101,
        party_b_id=102,
        amount_a_pennies=500,
        currency_a="USD",
        amount_b_pennies=400, # Needs 400 EUR
        currency_b="EUR",
        match_tick=1,
        rate_a_to_b=0.8
    )

    # Execute
    tx = system.execute_swap(match)

    # Verify Failure
    assert tx is None

    # Verify Balances Unchanged (Rollback or pre-check prevention)
    assert agent_a.get_balance("USD") == 1000
    assert agent_b.get_balance("EUR") == 100

def test_execute_swap_invalid_amounts(settlement_system):
    system, registry = settlement_system

    agent_a = MockFinancialAgent(101, {"USD": 1000})
    agent_b = MockFinancialAgent(102, {"EUR": 1000})

    def get_agent_side_effect(agent_id: Any):
        aid = int(agent_id)
        return {101: agent_a, 102: agent_b}.get(aid)

    registry.get_agent.side_effect = get_agent_side_effect

    match = FXMatchDTO(
        party_a_id=101,
        party_b_id=102,
        amount_a_pennies=-500, # Negative
        currency_a="USD",
        amount_b_pennies=400,
        currency_b="EUR",
        match_tick=1,
        rate_a_to_b=0.8
    )

    tx = system.execute_swap(match)
    assert tx is None

def test_execute_swap_missing_agent(settlement_system):
    system, registry = settlement_system

    agent_a = MockFinancialAgent(101, {"USD": 1000})

    def get_agent_side_effect(agent_id: Any):
        aid = int(agent_id)
        return {101: agent_a}.get(aid) # 102 Missing

    registry.get_agent.side_effect = get_agent_side_effect

    match = FXMatchDTO(
        party_a_id=101,
        party_b_id=102,
        amount_a_pennies=500,
        currency_a="USD",
        amount_b_pennies=400,
        currency_b="EUR",
        match_tick=1,
        rate_a_to_b=0.8
    )

    tx = system.execute_swap(match)
    assert tx is None
