import pytest
from unittest.mock import Mock, MagicMock

from modules.finance.api import BailoutCovenant, BailoutLoanDTO, InsufficientFundsError
from modules.finance.system import FinanceSystem

# A simple stub class for config attributes
class MockConfig:
    BAILOUT_PENALTY_PREMIUM = 0.05
    BAILOUT_REPAYMENT_RATIO = 0.5
    BAILOUT_COVENANT_RATIO = 0.5

    def get(self, key, default=None):
        # Handle "economy_params.KEY" by taking just "KEY"
        if "." in key:
            key = key.split(".")[-1]
        return getattr(self, key, default)

@pytest.fixture
def finance_test_environment():
    """Sets up a test environment with mocked financial entities."""
    mock_government = Mock()
    mock_government._assets = 1_000_000  # Starting with 1M in assets

    # We need to mock the withdraw/deposit methods to simulate transactions
    def withdraw(amount):
        if mock_government._assets >= amount:
            mock_government._assets -= amount
        else:
            raise InsufficientFundsError("Not enough assets.")
    def deposit(amount):
        mock_government._assets += amount

    mock_government.withdraw.side_effect = withdraw
    mock_government.deposit.side_effect = deposit

    mock_central_bank = Mock()
    mock_central_bank.get_base_rate.return_value = 0.02

    mock_bank = Mock()

    # Mock the Firm and its departments
    mock_firm = Mock()
    mock_firm.id = 1
    mock_firm._assets = 100_000
    mock_firm.total_debt = 0.0
    mock_firm.has_bailout_loan = False

    # Mock the finance department and its add_liability method
    mock_firm.finance = Mock()

    def add_liability_side_effect(amount, interest_rate):
        # Simulate the firm receiving cash and taking on debt
        mock_firm._assets += amount
        mock_firm.total_debt += amount

    mock_firm.finance.add_liability.side_effect = add_liability_side_effect

    # We need a deposit method on the firm for the _transfer to work
    def firm_deposit(amount):
        # This is separate from add_liability; it just handles the cash transfer part.
        # The liability logic is handled in the mocked add_liability.
        pass # In the real code, add_liability handles the asset increase.
             # In our mock, the side_effect for add_liability handles it, so we do nothing here.

    mock_firm.deposit.side_effect = firm_deposit


    config = MockConfig()

    # Instantiate the system with mocks
    finance_system = FinanceSystem(mock_government, mock_central_bank, mock_bank, config)

    return finance_system, mock_government, mock_firm

def test_grant_bailout_loan_success_and_covenant_type(finance_test_environment):
    """
    Tests that a bailout loan is granted successfully, all money flows are correct,
    and the returned DTO has the correct covenant type.
    """
    finance_system, mock_government, mock_firm = finance_test_environment
    initial_govt_assets = mock_government._assets
    initial_firm_assets = mock_firm._assets
    initial_firm_debt = mock_firm.total_debt
    loan_amount = 50_000

    # Act
    loan_dto = finance_system.grant_bailout_loan(mock_firm, loan_amount)

    # Assert - DTO and Covenant Type
    assert loan_dto is not None
    assert isinstance(loan_dto, BailoutLoanDTO)
    assert isinstance(loan_dto.covenants, BailoutCovenant)
    assert loan_dto.covenants.dividends_allowed is False
    assert loan_dto.covenants.mandatory_repayment == 0.5

    # Assert - Money Flow Verification
    # 1. Government assets should decrease
    assert mock_government._assets == initial_govt_assets - loan_amount
    # 2. Firm should have received the funds and taken on the liability
    mock_firm.finance.add_liability.assert_called_once()
    # 3. Verify firm's final state
    assert mock_firm._assets == initial_firm_assets + loan_amount
    assert mock_firm.total_debt == initial_firm_debt + loan_amount
    # 4. Firm should be marked as having a bailout loan
    assert mock_firm.has_bailout_loan is True

    # Assert - Regression check for money creation/destruction
    final_total_assets = mock_government._assets + mock_firm._assets
    initial_total_assets = initial_govt_assets + initial_firm_assets
    assert final_total_assets == initial_total_assets


def test_grant_bailout_loan_insufficient_government_funds(finance_test_environment):
    """
    Tests that the bailout loan is not granted if the government has insufficient funds.
    """
    finance_system, mock_government, mock_firm = finance_test_environment

    # Arrange: Government has less money than the loan amount
    loan_amount = 2_000_000
    mock_government._assets = 1_000_000 # Government has 1M, loan is 2M

    initial_govt_assets = mock_government._assets
    initial_firm_assets = mock_firm._assets
    initial_firm_debt = mock_firm.total_debt

    # Redefine the side effect for this specific test case to raise the error
    def limited_withdraw(amount):
        if mock_government._assets < amount:
            raise InsufficientFundsError("Test: Not enough funds")
        mock_government._assets -= amount
    mock_government.withdraw.side_effect = limited_withdraw

    # Act
    loan_dto = finance_system.grant_bailout_loan(mock_firm, loan_amount)

    # Assert
    # 1. No loan DTO should be returned
    assert loan_dto is None
    # 2. No money should have moved
    assert mock_government._assets == initial_govt_assets
    assert mock_firm._assets == initial_firm_assets
    assert mock_firm.total_debt == initial_firm_debt
    # 3. Firm should not be marked as having a loan
    assert mock_firm.has_bailout_loan is False
