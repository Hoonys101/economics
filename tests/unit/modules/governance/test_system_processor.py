import pytest
from unittest.mock import MagicMock

from modules.governance.processor import SystemCommandProcessor
from modules.governance.api import (
    SetTaxRateCommand,
    SetInterestRateCommand,
    SystemCommandType,
    IGovernment,
    ICentralBank,
    IFiscalPolicyHolder
)
from simulation.dtos.api import SimulationState

def test_set_tax_rate_corporate():
    processor = SystemCommandProcessor()

    # Setup state
    state = MagicMock(spec=SimulationState)
    state.time = 100

    # Setup Government
    gov = MagicMock(spec=IGovernment)
    gov.corporate_tax_rate = 0.1
    gov.income_tax_rate = 0.1

    # Setup Fiscal Policy
    fiscal_policy = MagicMock(spec=IFiscalPolicyHolder)
    fiscal_policy.corporate_tax_rate = 0.1
    fiscal_policy.income_tax_rate = 0.1
    gov.fiscal_policy = fiscal_policy

    state.primary_government = gov

    # Setup Command
    cmd = SetTaxRateCommand(
        command_type=SystemCommandType.SET_TAX_RATE,
        tax_type="corporate",
        new_rate=0.25
    )

    # Execute
    result_state = processor.execute(cmd, state)

    # Assert
    assert gov.corporate_tax_rate == 0.25
    assert gov.fiscal_policy.corporate_tax_rate == 0.25
    assert result_state == state

def test_set_tax_rate_income():
    processor = SystemCommandProcessor()

    # Setup state
    state = MagicMock(spec=SimulationState)
    state.time = 100

    # Setup Government
    gov = MagicMock(spec=IGovernment)
    gov.corporate_tax_rate = 0.1
    gov.income_tax_rate = 0.1

    # Setup Fiscal Policy
    fiscal_policy = MagicMock(spec=IFiscalPolicyHolder)
    fiscal_policy.corporate_tax_rate = 0.1
    fiscal_policy.income_tax_rate = 0.1
    gov.fiscal_policy = fiscal_policy

    state.primary_government = gov

    # Setup Command
    cmd = SetTaxRateCommand(
        command_type=SystemCommandType.SET_TAX_RATE,
        tax_type="income",
        new_rate=0.35
    )

    # Execute
    processor.execute(cmd, state)

    # Assert
    assert gov.income_tax_rate == 0.35
    assert gov.fiscal_policy.income_tax_rate == 0.35

def test_set_interest_rate_base_rate():
    processor = SystemCommandProcessor()

    # Setup state
    state = MagicMock(spec=SimulationState)
    state.time = 100

    # Setup Central Bank
    cb = MagicMock(spec=ICentralBank)
    cb.base_rate = 0.05
    state.central_bank = cb

    # Setup Command
    cmd = SetInterestRateCommand(
        command_type=SystemCommandType.SET_INTEREST_RATE,
        rate_type="base_rate",
        new_rate=0.08
    )

    # Execute
    result_state = processor.execute(cmd, state)

    # Assert
    assert cb.base_rate == 0.08
    assert result_state == state

def test_set_tax_rate_no_government_warning(caplog):
    import logging
    caplog.set_level(logging.ERROR)
    processor = SystemCommandProcessor()

    # Setup state with no government
    state = MagicMock(spec=SimulationState)
    state.time = 100
    state.primary_government = None

    # Setup Command
    cmd = SetTaxRateCommand(
        command_type=SystemCommandType.SET_TAX_RATE,
        tax_type="income",
        new_rate=0.35
    )

    # Execute
    processor.execute(cmd, state)

    # Assert
    assert "Government agent is None." in caplog.text

def test_set_tax_rate_invalid_protocol(caplog):
    import logging
    caplog.set_level(logging.ERROR)
    processor = SystemCommandProcessor()

    # Setup state with invalid government (doesn't implement IGovernment)
    state = MagicMock(spec=SimulationState)
    state.time = 100
    state.primary_government = object() # Not an IGovernment

    # Setup Command
    cmd = SetTaxRateCommand(
        command_type=SystemCommandType.SET_TAX_RATE,
        tax_type="income",
        new_rate=0.35
    )

    # Execute
    processor.execute(cmd, state)

    # Assert
    assert "does not satisfy IGovernment protocol" in caplog.text

def test_set_interest_rate_no_central_bank_warning(caplog):
    import logging
    caplog.set_level(logging.ERROR)
    processor = SystemCommandProcessor()

    # Setup state with no central bank
    state = MagicMock(spec=SimulationState)
    state.time = 100
    state.central_bank = None

    # Setup Command
    cmd = SetInterestRateCommand(
        command_type=SystemCommandType.SET_INTEREST_RATE,
        rate_type="base_rate",
        new_rate=0.08
    )

    # Execute
    processor.execute(cmd, state)

    # Assert
    assert "Central Bank agent is None" in caplog.text

def test_set_interest_rate_invalid_protocol(caplog):
    import logging
    caplog.set_level(logging.ERROR)
    processor = SystemCommandProcessor()

    # Setup state with invalid central bank
    state = MagicMock(spec=SimulationState)
    state.time = 100
    state.central_bank = object() # Not an ICentralBank

    # Setup Command
    cmd = SetInterestRateCommand(
        command_type=SystemCommandType.SET_INTEREST_RATE,
        rate_type="base_rate",
        new_rate=0.08
    )

    # Execute
    processor.execute(cmd, state)

    # Assert
    assert "does not satisfy ICentralBank protocol" in caplog.text
