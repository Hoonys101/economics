import pytest
from simulation.systems.settlement_system import SettlementSystem
from modules.finance.registry.account_registry import AccountRegistry
from modules.simulation.api import AgentID

def test_account_registry_integration():
    registry = AccountRegistry()
    settlement = SettlementSystem(account_registry=registry)

    bank_id = AgentID(1)
    agent_id = AgentID(100)

    # Register
    settlement.register_account(bank_id, agent_id)

    assert registry.get_account_holders(bank_id) == [agent_id]
    assert registry.get_agent_banks(agent_id) == [bank_id]
    assert settlement.get_account_holders(bank_id) == [agent_id]
    assert settlement.get_agent_banks(agent_id) == [bank_id]

    # Deregister
    settlement.deregister_account(bank_id, agent_id)
    assert registry.get_account_holders(bank_id) == []
    assert registry.get_agent_banks(agent_id) == []

def test_settlement_default_registry():
    settlement = SettlementSystem()
    assert isinstance(settlement.account_registry, AccountRegistry)

    bank_id = AgentID(2)
    agent_id = AgentID(200)

    settlement.register_account(bank_id, agent_id)
    assert settlement.get_account_holders(bank_id) == [agent_id]
