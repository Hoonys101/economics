import pytest
from unittest.mock import Mock, MagicMock

from modules.finance.api import BailoutCovenant, BailoutLoanDTO, GrantBailoutCommand, InsufficientFundsError
from modules.finance.system import FinanceSystem

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
    mock_government._assets = 1_000_000.0  # Starting with 1M in assets
    # Mock 'assets' property to return the float value
    type(mock_government).assets = PropertyMock(return_value=1_000_000.0)

    mock_central_bank = Mock()
    mock_central_bank.get_base_rate.return_value = 0.02

    mock_bank = Mock()

    # Mock the Firm and its departments
    mock_firm = Mock()
    mock_firm.id = "FIRM_MOCK"
    mock_firm._assets = 100_000.0
    mock_firm.total_debt = 0.0
    mock_firm.has_bailout_loan = False

    # Mock the finance department
    mock_firm.finance = Mock()

    config = MockConfig()

    # Instantiate the system with mocks
    finance_system = FinanceSystem(mock_government, mock_central_bank, mock_bank, config)

    return finance_system, mock_government, mock_firm

from unittest.mock import PropertyMock

def test_grant_bailout_loan_success_and_covenant_type(finance_test_environment):
    """
    Tests that a bailout loan request generates a valid GrantBailoutCommand.
    Note: Transaction generation and state updates are now handled by PolicyExecutionEngine,
    so we only verify the Command creation here.
    """
    finance_system, mock_government, mock_firm = finance_test_environment

    # Setup dynamic asset property for government to support check in request_bailout_loan
    type(mock_government).assets = PropertyMock(return_value=1_000_000.0)

    loan_amount = 50_000.0

    # Act
    # Use request_bailout_loan instead of deprecated grant_bailout_loan
    command = finance_system.request_bailout_loan(mock_firm, loan_amount)

    # Assert - Command and Covenant Type
    assert command is not None
    assert isinstance(command, GrantBailoutCommand)
    assert isinstance(command.covenants, BailoutCovenant)
    assert command.covenants.dividends_allowed is False
    assert command.covenants.mandatory_repayment == 0.5
    assert command.amount == loan_amount
    assert command.firm_id == mock_firm.id


def test_grant_bailout_loan_insufficient_government_funds(finance_test_environment):
    """
    Tests that the bailout loan command is not created if the government has insufficient funds.
    """
    finance_system, mock_government, mock_firm = finance_test_environment

    # Arrange: Government has less money than the loan amount
    loan_amount = 2_000_000.0
    # Set assets lower than loan amount
    type(mock_government).assets = PropertyMock(return_value=1_000_000.0)

    # Act
    command = finance_system.request_bailout_loan(mock_firm, loan_amount)

    # Assert
    assert command is None
