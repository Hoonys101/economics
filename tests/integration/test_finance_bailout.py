import pytest
from unittest.mock import Mock, MagicMock, PropertyMock

from modules.finance.api import BailoutCovenant, BailoutLoanDTO, GrantBailoutCommand, InsufficientFundsError
from modules.finance.system import FinanceSystem
from modules.system.api import DEFAULT_CURRENCY

# A simple stub class for config attributes
class MockConfig:
    def get(self, key, default=None):
        if key == "economy_params.BAILOUT_PENALTY_PREMIUM":
            return 0.05
        if key == "economy_params.BAILOUT_COVENANT_RATIO":
            return 0.5
        return default

@pytest.fixture
def finance_test_environment():
    """Sets up a test environment with mocked financial entities."""
    mock_government = Mock()
    mock_government.id = "GOVERNMENT_MOCK"
    # Mock wallet for FinanceSystem init sync
    mock_government.wallet.get_balance.return_value = 100000000 # 1M pennies

    mock_central_bank = Mock()
    mock_central_bank.get_base_rate.return_value = 0.02

    mock_bank = Mock()
    mock_bank.id = "BANK_MOCK"
    # Mock wallet for bank init sync
    mock_bank.wallet.get_balance.return_value = 1000000000
    mock_bank.base_rate = 0.03 # Set base rate as float

    # Mock the Firm and its departments
    mock_firm = Mock()
    mock_firm.id = "FIRM_MOCK"
    mock_firm.finance = Mock()

    config = MockConfig()

    # Instantiate the system with mocks
    finance_system = FinanceSystem(mock_government, mock_central_bank, mock_bank, config)

    return finance_system, mock_government, mock_firm

def test_grant_bailout_loan_success_and_covenant_type(finance_test_environment):
    """
    Tests that a bailout loan request generates a valid GrantBailoutCommand.
    Note: Transaction generation and state updates are now handled by PolicyExecutionEngine,
    so we only verify the Command creation here.
    """
    finance_system, mock_government, mock_firm = finance_test_environment

    loan_amount = 5000000 # 50,000.00 pennies

    # Update ledger directly as FinanceSystem uses it
    finance_system.ledger.treasury.balance[DEFAULT_CURRENCY] = 100000000 # 1M pennies

    # Act
    # Use request_bailout_loan instead of deprecated grant_bailout_loan
    command = finance_system.request_bailout_loan(mock_firm, loan_amount)

    # Assert - Command and Covenant Type
    assert command is not None
    assert isinstance(command, GrantBailoutCommand)
    assert isinstance(command.covenants, BailoutCovenant)
    assert command.covenants.dividends_allowed is False
    assert command.covenants.executive_bonus_allowed is False
    assert command.amount == loan_amount
    assert command.firm_id == mock_firm.id


def test_grant_bailout_loan_insufficient_government_funds(finance_test_environment):
    """
    Tests that the bailout loan command is not created if the government has insufficient funds.
    """
    finance_system, mock_government, mock_firm = finance_test_environment

    # Arrange: Government has less money than the loan amount
    loan_amount = 200000000 # 2M pennies

    # Update ledger
    finance_system.ledger.treasury.balance[DEFAULT_CURRENCY] = 100000000 # 1M pennies

    # Act
    command = finance_system.request_bailout_loan(mock_firm, loan_amount)

    # Assert
    assert command is None
