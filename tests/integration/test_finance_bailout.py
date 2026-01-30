import pytest
from unittest.mock import Mock, MagicMock

from modules.finance.api import BailoutCovenant, BailoutLoanDTO, InsufficientFundsError
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
    Tests that a bailout loan is granted successfully, generating the correct transactions
    and DTOs (Phase 3 Compliance).
    """
    finance_system, mock_government, mock_firm = finance_test_environment

    # Setup dynamic asset property for government to support check in grant_bailout_loan
    # The method checks if self.government.assets < amount
    type(mock_government).assets = PropertyMock(return_value=1_000_000.0)

    initial_firm_debt = mock_firm.total_debt
    loan_amount = 50_000.0
    current_tick = 10

    # Act
    # Update: method now returns (loan_dto, txs)
    loan_dto, txs = finance_system.grant_bailout_loan(mock_firm, loan_amount, current_tick)

    # Assert - DTO and Covenant Type
    assert loan_dto is not None
    assert isinstance(loan_dto, BailoutLoanDTO)
    assert isinstance(loan_dto.covenants, BailoutCovenant)
    assert loan_dto.covenants.dividends_allowed is False
    assert loan_dto.covenants.mandatory_repayment == 0.5

    # Assert - Transaction Verification (Phase 3 Compliance)
    # The system should generate a transaction, not mutate assets directly.
    assert len(txs) == 1
    tx = txs[0]
    assert tx.buyer_id == mock_government.id
    assert tx.seller_id == mock_firm.id
    assert tx.price == loan_amount
    assert tx.transaction_type == "bailout_loan"
    assert tx.time == current_tick

    # 2. Firm should have taken on the liability (Optimistic Update allowed for internal state like debt)
    assert mock_firm.total_debt == initial_firm_debt + loan_amount
    assert mock_firm.has_bailout_loan is True


def test_grant_bailout_loan_insufficient_government_funds(finance_test_environment):
    """
    Tests that the bailout loan is not granted if the government has insufficient funds.
    """
    finance_system, mock_government, mock_firm = finance_test_environment

    # Arrange: Government has less money than the loan amount
    loan_amount = 2_000_000.0
    # Set assets lower than loan amount
    type(mock_government).assets = PropertyMock(return_value=1_000_000.0)

    # Act
    loan_dto, txs = finance_system.grant_bailout_loan(mock_firm, loan_amount, current_tick=10)

    # Assert
    # 1. No loan DTO should be returned
    assert loan_dto is None
    # 2. No transactions should be generated
    assert len(txs) == 0
    # 3. Firm should not be marked as having a loan
    assert mock_firm.has_bailout_loan is False
