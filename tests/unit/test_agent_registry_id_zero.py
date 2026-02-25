import pytest
from unittest.mock import MagicMock, Mock
from modules.system.registry import AgentRegistry
from modules.system.api import IAgent, ISystemAgentRegistry, AgentID
from modules.system.constants import ID_CENTRAL_BANK

# Mock SimulationState
class MockSimulationState:
    def __init__(self):
        self.agents = {}
        self.estate_registry = None

def test_agent_registry_get_agent_zero():
    """Verify that get_agent(0) returns the correct agent and not None/False."""
    registry = AgentRegistry()
    state = MockSimulationState()
    registry.set_state(state)

    # Create a mock agent with ID 0
    central_bank = MagicMock(spec=IAgent)
    central_bank.id = ID_CENTRAL_BANK # 0
    central_bank.is_active = True

    # Manually add to state.agents (simulating legacy behavior)
    state.agents[ID_CENTRAL_BANK] = central_bank

    # Test get_agent(0)
    retrieved_agent = registry.get_agent(ID_CENTRAL_BANK)
    assert retrieved_agent is not None
    assert retrieved_agent.id == ID_CENTRAL_BANK
    assert retrieved_agent is central_bank

def test_agent_registry_implements_isystem_agent_registry():
    """Verify AgentRegistry implements ISystemAgentRegistry."""
    registry = AgentRegistry()
    assert isinstance(registry, ISystemAgentRegistry)

def test_register_system_agent():
    """Verify explicit registration of system agents."""
    registry = AgentRegistry()
    state = MockSimulationState()
    registry.set_state(state)

    central_bank = MagicMock(spec=IAgent)
    central_bank.id = ID_CENTRAL_BANK

    # Assuming register_system_agent is implemented
    registry.register_system_agent(central_bank)

    assert state.agents[ID_CENTRAL_BANK] is central_bank
    assert registry.get_agent(ID_CENTRAL_BANK) is central_bank
    assert registry.get_system_agent(ID_CENTRAL_BANK) is central_bank

def test_get_agent_none_handling():
    """Verify get_agent handles None correctly."""
    registry = AgentRegistry()
    state = MockSimulationState()
    registry.set_state(state)

    assert registry.get_agent(None) is None
