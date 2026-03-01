import pytest
from unittest.mock import MagicMock
from modules.simulation.tick_context_adapter import TickContextAdapter

def test_tick_context_adapter_commerce_protocol():
    """Verify ICommerceTickContext attributes map correctly to state."""
    mock_state = MagicMock()
    mock_state.time = 42
    mock_state.market_data = {"APPLES": {"price": 10}}
    mock_state.goods_data = {"APPLES": {"type": "food"}}

    adapter = TickContextAdapter(mock_state)

    assert adapter.current_time == 42
    assert adapter.market_data == {"APPLES": {"price": 10}}
    assert adapter.goods_data == {"APPLES": {"type": "food"}}

def test_tick_context_adapter_governance_protocol():
    """Verify IGovernanceTickContext attributes map correctly to state."""
    mock_state = MagicMock()
    mock_state.time = 42
    mock_state.government = MagicMock()
    mock_state.taxation_system = MagicMock()

    adapter = TickContextAdapter(mock_state)

    assert adapter.primary_government == mock_state.government
    assert adapter.taxation_system == mock_state.taxation_system

def test_tick_context_adapter_finance_protocol():
    """Verify IFinanceTickContext attributes map correctly to state."""
    mock_state = MagicMock()
    mock_state.time = 42
    mock_state.bank = MagicMock()
    mock_state.central_bank = MagicMock()
    mock_state.monetary_ledger = MagicMock()
    mock_state.saga_orchestrator = MagicMock()

    adapter = TickContextAdapter(mock_state)

    assert adapter.bank == mock_state.bank
    assert adapter.central_bank == mock_state.central_bank
    assert adapter.monetary_ledger == mock_state.monetary_ledger
    assert adapter.saga_orchestrator == mock_state.saga_orchestrator

def test_tick_context_adapter_mutation_protocol():
    """Verify IMutationTickContext attributes map correctly to state queues."""
    class MockState:
        def __init__(self):
            self.transactions = []
            self.effects_queue = []
            self.god_commands = []

    mock_state = MockState()

    adapter = TickContextAdapter(mock_state)

    adapter.append_transaction({"type": "BUY"})
    assert mock_state.transactions == [{"type": "BUY"}]

    adapter.append_effect({"type": "SHOCK"})
    assert mock_state.effects_queue == [{"type": "SHOCK"}]

    adapter.append_god_command({"type": "DESTROY"})
    assert mock_state.god_commands == [{"type": "DESTROY"}]

def test_tick_context_adapter_legacy_fallback():
    """Verify that unmapped attributes correctly fall back to the state."""
    mock_state = MagicMock()
    mock_state.some_legacy_attribute = "legacy_value"

    adapter = TickContextAdapter(mock_state)

    assert adapter.some_legacy_attribute == "legacy_value"

def test_tick_context_adapter_missing_attribute():
    """Verify AttributeError is raised when attribute is not in state."""
    mock_state = MagicMock()
    del mock_state.missing_attribute

    adapter = TickContextAdapter(mock_state)

    with pytest.raises(AttributeError):
        _ = adapter.missing_attribute
