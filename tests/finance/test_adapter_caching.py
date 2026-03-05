import pytest
from unittest.mock import MagicMock, Mock
from modules.finance.transaction.adapter import RegistryAccountAccessor, FinancialAgentAdapter, FinancialEntityAdapter
from modules.finance.transaction.api import InvalidAccountError
from modules.finance.api import IFinancialAgent, IFinancialEntity
from modules.system.api import IAgentRegistry, AgentID

class DummyAgent(IFinancialAgent):
    def __init__(self, agent_id: AgentID):
        self.id = agent_id
    def get_balance(self, currency): pass
    def _deposit(self, amount, currency): pass
    def _withdraw(self, amount, currency): pass

class DummyEntity(IFinancialEntity):
    def __init__(self, entity_id: AgentID):
        self.id = entity_id
    @property
    def balance_pennies(self): return 0
    def deposit(self, amount, currency): pass
    def withdraw(self, amount, currency): pass

class DummyNonFinancial:
    def __init__(self, id: AgentID):
        self.id = id

def test_registry_account_accessor_caching():
    # Setup
    registry_mock = MagicMock(spec=IAgentRegistry)
    accessor = RegistryAccountAccessor(registry=registry_mock)

    agent_id = 1
    entity_id = 2
    none_id = 3

    agent = DummyAgent(agent_id)
    entity = DummyEntity(entity_id)
    none_agent = DummyNonFinancial(none_id)

    # Mock registry returns
    def get_agent_side_effect(aid):
        if aid == agent_id: return agent
        if aid == entity_id: return entity
        if aid == none_id: return none_agent
        return None

    registry_mock.get_agent.side_effect = get_agent_side_effect

    # 1. Test caching for Agent
    assert len(accessor._protocol_cache) == 0
    participant1 = accessor.get_participant(agent_id)
    assert isinstance(participant1, FinancialAgentAdapter)
    assert DummyAgent in accessor._protocol_cache
    assert accessor._protocol_cache[DummyAgent] == 'agent'

    # Second time should hit cache
    participant2 = accessor.get_participant(agent_id)
    assert isinstance(participant2, FinancialAgentAdapter)

    # 2. Test caching for Entity
    assert DummyEntity not in accessor._protocol_cache
    participant3 = accessor.get_participant(entity_id)
    assert isinstance(participant3, FinancialEntityAdapter)
    assert DummyEntity in accessor._protocol_cache
    assert accessor._protocol_cache[DummyEntity] == 'entity'

    # Second time should hit cache
    participant4 = accessor.get_participant(entity_id)
    assert isinstance(participant4, FinancialEntityAdapter)

    # 3. Test caching for Non-Financial
    assert DummyNonFinancial not in accessor._protocol_cache
    with pytest.raises(InvalidAccountError):
        accessor.get_participant(none_id)
    assert DummyNonFinancial in accessor._protocol_cache
    assert accessor._protocol_cache[DummyNonFinancial] == 'none'

    # Second time should hit cache and still raise
    with pytest.raises(InvalidAccountError):
        accessor.get_participant(none_id)
