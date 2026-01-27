import pytest
from unittest.mock import MagicMock, patch
from simulation.bank import Bank, Loan
from modules.finance.api import (
    InsufficientFundsError,
    ICreditScoringService,
    BorrowerProfileDTO,
    CreditAssessmentResultDTO,
    LoanRollbackError
)

@pytest.fixture(autouse=True)
def mock_logger():
    with patch("simulation.bank.logging.getLogger") as mock_get_logger:
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        yield mock_logger_instance

from modules.common.config_manager.impl import ConfigManagerImpl
from pathlib import Path

@pytest.fixture
def config_manager(tmp_path: Path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return ConfigManagerImpl(config_dir)

@pytest.fixture
def mock_credit_scoring_service():
    service = MagicMock(spec=ICreditScoringService)
    # Default approval
    service.assess_creditworthiness.return_value = {
        "is_approved": True,
        "max_loan_amount": 100000.0,
        "reason": None
    }
    return service

@pytest.fixture
def bank_instance(config_manager, mock_credit_scoring_service):
    # Initialize with enough assets for tests
    return Bank(
        id=1,
        initial_assets=10000.0,
        config_manager=config_manager,
        credit_scoring_service=mock_credit_scoring_service
    )

class TestBank:
    def test_initialization(self, bank_instance: Bank):
        assert bank_instance.id == 1
        assert bank_instance.assets == 10000.0
        assert bank_instance.loans == {}
        assert bank_instance.next_loan_id == 0

    def test_grant_loan_successful(self, bank_instance: Bank, mock_credit_scoring_service):
        bank_instance.config_manager.set_value_for_test("bank_defaults.initial_base_annual_rate", 0.05)
        initial_assets = bank_instance.assets
        borrower_id = "101"
        amount = 1000.0

        profile = BorrowerProfileDTO(
            borrower_id=borrower_id, gross_income=100.0,
            existing_debt_payments=0.0, collateral_value=0.0, existing_assets=10.0
        )

        # Call with correct signature
        loan_info = bank_instance.grant_loan(
            borrower_id=borrower_id,
            amount=amount,
            interest_rate=0.07,
            due_tick=50,
            borrower_profile=profile
        )

        assert loan_info is not None
        assert loan_info["borrower_id"] == borrower_id
        assert loan_info["original_amount"] == 1000.0

        # Verify Credit Service called
        mock_credit_scoring_service.assess_creditworthiness.assert_called_once()

        # Verify Deposit Created (Money Creation)
        assert len(bank_instance.deposits) == 1
        dep = list(bank_instance.deposits.values())[0]
        assert dep.depositor_id == int(borrower_id)
        assert dep.amount == amount

        # Verify Reserves (Assets) Check - Should be unchanged (Fractional Reserve)
        assert bank_instance.assets == initial_assets

    def test_grant_loan_denied_credit(self, bank_instance, mock_credit_scoring_service):
        # Setup mock to deny
        mock_credit_scoring_service.assess_creditworthiness.return_value = {
            "is_approved": False,
            "max_loan_amount": 0.0,
            "reason": "Risk too high"
        }

        profile = BorrowerProfileDTO(borrower_id="101", gross_income=100.0, existing_debt_payments=100.0, collateral_value=0.0, existing_assets=0.0)

        loan_info = bank_instance.grant_loan("101", 1000.0, 0.05, borrower_profile=profile)
        assert loan_info is None
        assert len(bank_instance.loans) == 0

    def test_grant_loan_insufficient_reserves(self, bank_instance):
        # Default reserve ratio is 0.1
        # Assets 10000.
        # Deposits 0.
        # Requested 200,000.
        # New Deposit = 200,000. Required Reserve = 20,000.
        # Assets 10,000 < 20,000. Fail.

        borrower_id = "101"
        amount = 200000.0
        profile = BorrowerProfileDTO(borrower_id=borrower_id, gross_income=1000.0, existing_debt_payments=0.0, collateral_value=0.0, existing_assets=0.0)

        loan_info = bank_instance.grant_loan(borrower_id, amount, 0.05, borrower_profile=profile)

        assert loan_info is None
        assert len(bank_instance.loans) == 0

    def test_grant_loan_multiple_loans(self, bank_instance):
        profile = BorrowerProfileDTO(borrower_id="101", gross_income=1000.0, existing_debt_payments=0.0, collateral_value=0.0, existing_assets=0.0)

        bank_instance.grant_loan("101", 1000.0, 0.05, borrower_profile=profile)
        bank_instance.grant_loan("102", 500.0, 0.05, borrower_profile=profile)

        assert len(bank_instance.loans) == 2
        assert "loan_0" in bank_instance.loans
        assert "loan_1" in bank_instance.loans

    def test_deposit_from_customer(self, bank_instance):
        depositor_id = 202
        amount = 500.0
        initial_assets = bank_instance.assets

        deposit_id = bank_instance.deposit_from_customer(depositor_id, amount)

        assert deposit_id is not None
        assert deposit_id.startswith("dep_")
        assert len(bank_instance.deposits) == 1
        # Check that assets were NOT increased (handled by Transaction)
        assert bank_instance.assets == initial_assets

        deposit = bank_instance.deposits[deposit_id]
        assert deposit.depositor_id == depositor_id
        assert deposit.amount == amount

    def test_withdraw_for_customer_success(self, bank_instance):
        depositor_id = 202
        amount = 500.0

        # Setup: Deposit first
        deposit_id = bank_instance.deposit_from_customer(depositor_id, amount)

        # Act: Withdraw
        success = bank_instance.withdraw_for_customer(depositor_id, 200.0)

        assert success is True
        assert bank_instance.deposits[deposit_id].amount == 300.0
        # Check assets (not changed by this method directly)
        assert bank_instance.assets == 10000.0

    def test_withdraw_for_customer_insufficient(self, bank_instance):
        depositor_id = 202
        amount = 500.0
        bank_instance.deposit_from_customer(depositor_id, amount)

        success = bank_instance.withdraw_for_customer(depositor_id, 600.0)
        assert success is False

    def test_financial_entity_deposit(self, bank_instance):
        initial = bank_instance.assets
        bank_instance.deposit(500.0)
        assert bank_instance.assets == initial + 500.0

    def test_financial_entity_withdraw(self, bank_instance):
        initial = bank_instance.assets
        bank_instance.withdraw(500.0)
        assert bank_instance.assets == initial - 500.0

    def test_financial_entity_withdraw_insufficient(self, bank_instance):
        with pytest.raises(InsufficientFundsError):
            bank_instance.withdraw(bank_instance.assets + 1000.0)

    def test_run_tick_returns_transactions(self, bank_instance):
        # Setup: Loan and Deposit
        borrower_id = 101
        depositor_id = 202

        # Create Loan with dummy profile
        profile = BorrowerProfileDTO(borrower_id=str(borrower_id), gross_income=1000.0, existing_debt_payments=0.0, collateral_value=0.0, existing_assets=0.0)
        bank_instance.grant_loan(str(borrower_id), 1000.0, 0.05, borrower_profile=profile)

        bank_instance.deposit_from_customer(depositor_id, 500.0)

        # Mock Agents
        mock_borrower = MagicMock()
        mock_borrower.id = borrower_id
        mock_borrower.assets = 100.0 # Enough to pay interest
        mock_borrower.is_active = True

        mock_depositor = MagicMock()
        mock_depositor.id = depositor_id
        mock_depositor.is_active = True

        agents = {borrower_id: mock_borrower, depositor_id: mock_depositor}

        # Act
        transactions = bank_instance.run_tick(agents, current_tick=1)

        # Assert
        assert len(transactions) >= 2 # Interest Payment (Loan) + Interest Payment (Deposit)

        # Check types
        tx_types = [tx.transaction_type for tx in transactions]
        assert "loan_interest" in tx_types
        assert "deposit_interest" in tx_types

        # Check assets NOT modified
        assert bank_instance.assets == 10000.0

    def test_void_loan_failure_raises_exception(self, bank_instance):
        # Setup: Create a loan manually (bypassing normal grant_loan to simulate broken link)
        # Note: We need to inject a loan without a valid deposit to test failure
        from simulation.bank import Loan
        loan_id = "loan_broken_link"
        bank_instance.loans[loan_id] = Loan(
            borrower_id=999,
            principal=1000.0,
            remaining_balance=1000.0,
            annual_interest_rate=0.05,
            term_ticks=50,
            start_tick=0,
            created_deposit_id="non_existent_deposit_id"
        )

        with pytest.raises(LoanRollbackError):
            bank_instance.void_loan(loan_id)

        # Verify loan was NOT deleted (Atomic Rollback)
        assert loan_id in bank_instance.loans
