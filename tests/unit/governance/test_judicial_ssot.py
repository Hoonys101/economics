import pytest
from unittest.mock import MagicMock, call
from modules.governance.judicial.system import JudicialSystem
from modules.governance.judicial.api import LoanDefaultedEvent
from modules.system.event_bus.api import IEventBus
from simulation.finance.api import ISettlementSystem
from modules.system.api import IAgentRegistry, DEFAULT_CURRENCY
from modules.finance.api import IShareholderRegistry, IFinancialAgent
from modules.common.config_manager.api import ConfigManager

@pytest.fixture
def mock_deps():
    event_bus = MagicMock(spec=IEventBus)
    settlement = MagicMock(spec=ISettlementSystem)
    registry = MagicMock(spec=IAgentRegistry)
    shareholder_registry = MagicMock(spec=IShareholderRegistry)
    config_mgr = MagicMock(spec=ConfigManager)
    return event_bus, settlement, registry, shareholder_registry, config_mgr

def test_waterfall_cash_only_ssot(mock_deps):
    event_bus, settlement, registry, shareholder_registry, config_mgr = mock_deps

    system = JudicialSystem(event_bus, settlement, registry, shareholder_registry, config_mgr)

    agent_id = 101
    creditor_id = 202
    debt_amount = 1000
    loan_id = "LOAN_001"
    tick = 10

    # SSoT Setup: Agent has sufficient balance
    settlement.get_balance.return_value = 5000 # 5000 pennies
    settlement.transfer.return_value = True # Transfer success

    # Mock Agents
    mock_agent = MagicMock(spec=IFinancialAgent)
    mock_creditor = MagicMock(spec=IFinancialAgent)

    def get_agent_side_effect(aid):
        if aid == agent_id: return mock_agent
        if aid == creditor_id: return mock_creditor
        return None
    registry.get_agent.side_effect = get_agent_side_effect

    event = LoanDefaultedEvent(
        event_type="LOAN_DEFAULTED",
        tick=tick,
        agent_id=agent_id,
        loan_id=loan_id,
        defaulted_amount=debt_amount,
        creditor_id=creditor_id
    )

    result = system.handle_default(event)

    # Assertions
    # 1. Check Settlement System Interaction
    settlement.get_balance.assert_called_with(agent_id, DEFAULT_CURRENCY)
    settlement.transfer.assert_called_once_with(
        debit_agent=mock_agent,
        credit_agent=mock_creditor,
        amount=debt_amount,
        memo=f"Seizure: Default {loan_id} (Cash Stage 1)",
        tick=tick
    )

    # 2. Check Result DTO
    assert result.seized_cash == 1000
    assert result.remaining_debt == 0
    assert result.is_fully_recovered is True

    # 3. Verify Purity (No direct agent balance access)
    # Since we used spec=IFinancialAgent, if the code tried to access 'wallet' it would fail if not in spec,
    # or if we check calls.
    # We can check that get_balance on agent was NOT called.
    # Note: IFinancialAgent HAS get_balance. We want to ensure it wasn't called.
    mock_agent.get_balance.assert_not_called()

def test_waterfall_partial_cash(mock_deps):
    event_bus, settlement, registry, shareholder_registry, config_mgr = mock_deps

    system = JudicialSystem(event_bus, settlement, registry, shareholder_registry, config_mgr)

    agent_id = 101
    creditor_id = 202
    debt_amount = 1000
    agent_balance = 400

    # SSoT Setup: Agent has INSUFFICIENT balance
    settlement.get_balance.return_value = agent_balance
    settlement.transfer.return_value = True

    mock_agent = MagicMock(spec=IFinancialAgent)
    mock_creditor = MagicMock(spec=IFinancialAgent)

    def get_agent_side_effect(aid):
        if aid == agent_id: return mock_agent
        if aid == creditor_id: return mock_creditor
        return None
    registry.get_agent.side_effect = get_agent_side_effect

    event = LoanDefaultedEvent(
        event_type="LOAN_DEFAULTED",
        tick=10,
        agent_id=agent_id,
        loan_id="LOAN_002",
        defaulted_amount=debt_amount,
        creditor_id=creditor_id
    )

    result = system.handle_default(event)

    # Assertions
    settlement.transfer.assert_called_with(
        debit_agent=mock_agent,
        credit_agent=mock_creditor,
        amount=agent_balance, # 400
        memo="Seizure: Default LOAN_002 (Cash Stage 1)",
        tick=10
    )

    assert result.seized_cash == 400
    assert result.remaining_debt == 600
    assert result.is_fully_recovered is False
