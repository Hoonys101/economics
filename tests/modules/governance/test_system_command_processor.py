import pytest
from unittest.mock import MagicMock
from modules.governance.api import SystemCommandType, SetTaxRateCommand, SetInterestRateCommand, IGovernment, ICentralBank
from modules.governance.processor import SystemCommandProcessor
from simulation.dtos.api import SimulationState

@pytest.fixture
def mock_simulation_state():
    state = MagicMock(spec=SimulationState)
    state.time = 100
    # Use MagicMock(spec=IGovernment) to satisfy protocol check
    state.government = MagicMock(spec=IGovernment)
    state.central_bank = MagicMock(spec=ICentralBank)

    # Setup government attributes
    state.government.corporate_tax_rate = 0.2
    state.government.income_tax_rate = 0.1
    state.government.fiscal_policy = MagicMock()
    state.government.fiscal_policy.corporate_tax_rate = 0.2
    state.government.fiscal_policy.income_tax_rate = 0.1

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
    processor = SystemCommandProcessor()
    command = SetTaxRateCommand(
        tax_type='corporate',
        new_rate=0.25
    )

    # Should log error but not crash
    processor.execute(command, mock_simulation_state)

def test_protocol_guardrails(mock_simulation_state):
    # Setup an object that does NOT satisfy IGovernment
    mock_simulation_state.government = MagicMock() # Not spec=IGovernment
    # Explicitly remove an attribute required by IGovernment to fail isinstance check
    # IGovernment requires: corporate_tax_rate, income_tax_rate, fiscal_policy
    # MagicMock has all attributes by default.
    # To make isinstance(mock, Protocol) fail, we need to ensure it DOESN'T implement it.
    # runtime_checkable checks for presence of attributes.
    # deleting an attribute from MagicMock instance is tricky because it regenerates on access unless we del it from __dict__ or spec it differently.

    # Better approach: Create a dummy class that misses attributes
    class NotGovernment:
        pass

    mock_simulation_state.government = NotGovernment()

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
    # and that the logger was called (if we could verify logs, but here just ensure safe execution).

    # If logic proceeded, it would have tried to access attributes on NotGovernment and crashed (AttributeError).
    # Since it didn't crash, the guardrail worked (or it crashed inside and was caught? No, execute doesn't catch generic Exception).

    pass
