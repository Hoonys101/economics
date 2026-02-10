import pytest
from unittest.mock import MagicMock
from modules.governance.api import SystemCommandType, SetTaxRateCommand, SetInterestRateCommand
from modules.governance.processor import SystemCommandProcessor
from simulation.dtos.api import SimulationState

@pytest.fixture
def mock_simulation_state():
    state = MagicMock(spec=SimulationState)
    state.time = 100
    state.government = MagicMock()
    state.central_bank = MagicMock()

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
    command: SetTaxRateCommand = {
        'command_type': SystemCommandType.SET_TAX_RATE,
        'tax_type': 'corporate',
        'new_rate': 0.25
    }

    processor.execute(command, mock_simulation_state)

    assert mock_simulation_state.government.corporate_tax_rate == 0.25
    assert mock_simulation_state.government.fiscal_policy.corporate_tax_rate == 0.25

def test_set_income_tax_rate(mock_simulation_state):
    processor = SystemCommandProcessor()
    command: SetTaxRateCommand = {
        'command_type': SystemCommandType.SET_TAX_RATE,
        'tax_type': 'income',
        'new_rate': 0.15
    }

    processor.execute(command, mock_simulation_state)

    assert mock_simulation_state.government.income_tax_rate == 0.15
    assert mock_simulation_state.government.fiscal_policy.income_tax_rate == 0.15

def test_set_base_interest_rate(mock_simulation_state):
    processor = SystemCommandProcessor()
    command: SetInterestRateCommand = {
        'command_type': SystemCommandType.SET_INTEREST_RATE,
        'rate_type': 'base_rate',
        'new_rate': 0.03
    }

    processor.execute(command, mock_simulation_state)

    assert mock_simulation_state.central_bank.base_rate == 0.03

def test_ignore_unknown_tax_type(mock_simulation_state):
    processor = SystemCommandProcessor()
    command: SetTaxRateCommand = {
        'command_type': SystemCommandType.SET_TAX_RATE,
        'tax_type': 'invalid', # type: ignore
        'new_rate': 0.99
    }

    # Should not raise error and should not modify state
    processor.execute(command, mock_simulation_state)

    assert mock_simulation_state.government.corporate_tax_rate == 0.2
    assert mock_simulation_state.government.income_tax_rate == 0.1

def test_missing_government(mock_simulation_state):
    mock_simulation_state.government = None
    processor = SystemCommandProcessor()
    command: SetTaxRateCommand = {
        'command_type': SystemCommandType.SET_TAX_RATE,
        'tax_type': 'corporate',
        'new_rate': 0.25
    }

    # Should log error but not crash
    processor.execute(command, mock_simulation_state)
