import pytest
from unittest.mock import MagicMock
from modules.governance.api import SystemCommandType, SetTaxRateCommand, SetInterestRateCommand, IGovernment, ICentralBank
from modules.governance.processor import SystemCommandProcessor
from simulation.dtos.api import SimulationState
from simulation.agents.government import Government
from simulation.systems.central_bank_system import CentralBankSystem
from modules.government.dtos import FiscalPolicyDTO

@pytest.fixture
def mock_simulation_state():
    state = MagicMock(spec=SimulationState)
    state.time = 100
    # Use MagicMock() without spec for Government to satisfy Protocol check
    # (MagicMock(spec=Class) has issues with runtime_checkable Protocols)
    state.government = MagicMock()
    state.central_bank = MagicMock(spec=CentralBankSystem)

    # Setup government attributes
    state.primary_government = state.government
    state.government.corporate_tax_rate = 0.2
    state.government.income_tax_rate = 0.1
    state.government.fiscal_policy = MagicMock(spec=FiscalPolicyDTO)
    state.government.fiscal_policy.corporate_tax_rate = 0.2
    state.government.fiscal_policy.income_tax_rate = 0.1

    # Satisfy IGovernment protocol
    from modules.system.api import DEFAULT_CURRENCY
    state.government.expenditure_this_tick = {DEFAULT_CURRENCY: 0}
    state.government.revenue_this_tick = {DEFAULT_CURRENCY: 0}
    state.government.total_debt = 0
    state.government.total_wealth = 0
    state.government.state = MagicMock()
    state.government.make_policy_decision = MagicMock()
    state.government.id = 1
    state.government.name = "MockGov"
    state.government.is_active = True

    # Setup central bank attributes
    state.central_bank.base_rate = 0.05
    return state

def test_set_corporate_tax_rate(mock_simulation_state):
    processor = SystemCommandProcessor()
    command = SetTaxRateCommand(
        tax_type='corporate',
        new_rate=0.25
    )

    processor.execute(command, mock_simulation_state)

    assert mock_simulation_state.government.corporate_tax_rate == 0.25
    assert mock_simulation_state.government.fiscal_policy.corporate_tax_rate == 0.25

def test_set_income_tax_rate(mock_simulation_state):
    processor = SystemCommandProcessor()
    command = SetTaxRateCommand(
        tax_type='income',
        new_rate=0.15
    )

    processor.execute(command, mock_simulation_state)

    assert mock_simulation_state.government.income_tax_rate == 0.15
    assert mock_simulation_state.government.fiscal_policy.income_tax_rate == 0.15

def test_set_base_interest_rate(mock_simulation_state):
    processor = SystemCommandProcessor()
    command = SetInterestRateCommand(
        rate_type='base_rate',
        new_rate=0.03
    )

    processor.execute(command, mock_simulation_state)

    assert mock_simulation_state.central_bank.base_rate == 0.03

def test_missing_government(mock_simulation_state):
    mock_simulation_state.government = None
    mock_simulation_state.primary_government = None
    processor = SystemCommandProcessor()
    command = SetTaxRateCommand(
        tax_type='corporate',
        new_rate=0.25
    )

    # Should log error but not crash
    processor.execute(command, mock_simulation_state)

def test_protocol_guardrails(mock_simulation_state):
    # Setup an object that does NOT satisfy IGovernment
    # We use a dummy class that definitely doesn't implement the protocol
    class NotGovernment:
        pass

    mock_simulation_state.government = NotGovernment()
    mock_simulation_state.primary_government = mock_simulation_state.government

    processor = SystemCommandProcessor()
    command = SetTaxRateCommand(
        tax_type='corporate',
        new_rate=0.25
    )

    # Execute
    processor.execute(command, mock_simulation_state)

    # Assert nothing happened (because it returned early)
    # Since NotGovernment doesn't have tax rates, we can't check them.
    # But we can check that no exception was raised (handled gracefully)

    # We can also verify that execute returned safely.
    pass
