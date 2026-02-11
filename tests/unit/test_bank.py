import pytest
from unittest.mock import MagicMock, patch, ANY
from simulation.bank import Bank
from modules.finance.managers.loan_manager import _Loan
from modules.finance.api import (
    InsufficientFundsError,
    ICreditScoringService,
    BorrowerProfileDTO,
    LoanRollbackError,
    IFinancialAgent
)
from modules.system.event_bus.api import IEventBus
from modules.system.api import DEFAULT_CURRENCY

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
def mock_event_bus():
    return MagicMock(spec=IEventBus)

@pytest.fixture
def bank_instance(config_manager, mock_credit_scoring_service, mock_event_bus):
    # Initialize with enough assets for tests
    return Bank(
        id=1,
        initial_assets=10000.0,
        config_manager=config_manager,
        credit_scoring_service=mock_credit_scoring_service,
        event_bus=mock_event_bus
    )

class TestBank:
    def test_initialization(self, bank_instance: Bank):
        assert bank_instance.id == 1
        assert bank_instance.assets == 10000.0
        # Check manager internal state instead of bank.loans
        assert bank_instance.loan_manager._loans == {}
        # Bank no longer exposes next_loan_id directly, manager handles it
        assert bank_instance.loan_manager._next_loan_id == 0

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
        grant_result = bank_instance.grant_loan(
            borrower_id=borrower_id,
            amount=amount,
            interest_rate=0.07,
            due_tick=50,
            borrower_profile=profile
        )

        assert grant_result is not None
        loan_info, tx = grant_result
        assert loan_info["borrower_id"] == borrower_id
        assert loan_info["original_amount"] == 1000.0
        assert tx.transaction_type == "credit_creation"

        # Verify Credit Service called
        mock_credit_scoring_service.assess_creditworthiness.assert_called_once()

        # Verify Deposit Created (Money Creation)
        # Bank uses DepositManager
        assert bank_instance.deposit_manager.get_total_deposits() == amount

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

        grant_result = bank_instance.grant_loan("101", 1000.0, 0.05, borrower_profile=profile)
        assert grant_result is None
        assert len(bank_instance.loan_manager._loans) == 0

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

        grant_result = bank_instance.grant_loan(borrower_id, amount, 0.05, borrower_profile=profile)

        assert grant_result is None
        assert len(bank_instance.loan_manager._loans) == 0

    def test_grant_loan_multiple_loans(self, bank_instance):
        profile = BorrowerProfileDTO(borrower_id="101", gross_income=1000.0, existing_debt_payments=0.0, collateral_value=0.0, existing_assets=0.0)

        bank_instance.grant_loan("101", 1000.0, 0.05, borrower_profile=profile)
        bank_instance.grant_loan("102", 500.0, 0.05, borrower_profile=profile)

        assert len(bank_instance.loan_manager._loans) == 2
        assert "loan_0" in bank_instance.loan_manager._loans
        assert "loan_1" in bank_instance.loan_manager._loans

    def test_deposit_from_customer(self, bank_instance):
        depositor_id = 202
        amount = 500.0
        initial_assets = bank_instance.assets

        deposit_id = bank_instance.deposit_from_customer(depositor_id, amount)

        assert deposit_id is not None
        assert deposit_id.startswith("dep_")
        assert bank_instance.deposit_manager.get_total_deposits() == amount
        # Check that assets were NOT increased (handled by Transaction)
        assert bank_instance.assets == initial_assets

        balance = bank_instance.deposit_manager.get_balance(depositor_id)
        assert balance == amount

    def test_withdraw_for_customer_success(self, bank_instance):
        depositor_id = 202
        amount = 500.0

        # Setup: Deposit first
        deposit_id = bank_instance.deposit_from_customer(depositor_id, amount)

        # Act: Withdraw
        success = bank_instance.withdraw_for_customer(depositor_id, 200.0)

        assert success is True
        assert bank_instance.deposit_manager.get_balance(depositor_id) == 300.0
        # Check assets (reduced by withdrawal amount due to physical settlement)
        assert bank_instance.assets == 9800.0

    def test_withdraw_for_customer_insufficient(self, bank_instance):
        depositor_id = 202
        amount = 500.0
        bank_instance.deposit_from_customer(depositor_id, amount)

        success = bank_instance.withdraw_for_customer(depositor_id, 600.0)
        assert success is False

    def test_financial_entity_deposit(self, bank_instance):
        initial = bank_instance.get_balance(DEFAULT_CURRENCY)
        bank_instance.deposit(500.0)
        assert bank_instance.get_balance(DEFAULT_CURRENCY) == initial + 500.0

    def test_financial_entity_withdraw(self, bank_instance):
        initial = bank_instance.get_balance(DEFAULT_CURRENCY)
        bank_instance.withdraw(500.0)
        assert bank_instance.get_balance(DEFAULT_CURRENCY) == initial - 500.0

    def test_financial_entity_withdraw_insufficient(self, bank_instance):
        with pytest.raises(InsufficientFundsError):
            bank_instance.withdraw(bank_instance.get_balance(DEFAULT_CURRENCY) + 1000.0)

    def test_run_tick_returns_transactions(self, bank_instance):
        # Setup: Loan and Deposit
        borrower_id = 101
        depositor_id = 202

        # Create Loan with dummy profile
        profile = BorrowerProfileDTO(borrower_id=borrower_id, gross_income=1000.0, existing_debt_payments=0.0, collateral_value=0.0, existing_assets=0.0)
        bank_instance.grant_loan(borrower_id, 1000.0, 0.05, borrower_profile=profile)

        bank_instance.deposit_from_customer(depositor_id, 500.0)

        # Mock Agents
        mock_borrower = MagicMock(spec=IFinancialAgent)
        mock_borrower.id = borrower_id
        # IFinancialAgent uses get_balance
        mock_borrower.get_balance.return_value = 100.0
        mock_borrower.is_active = True

        mock_depositor = MagicMock(spec=IFinancialAgent)
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

        # Check assets modified (Interest collected > Interest paid)
        assert bank_instance.get_balance(DEFAULT_CURRENCY) > 10000.0

        # Verify Borrower Withdraw called with Currency
        mock_borrower.withdraw.assert_called_with(ANY, currency=DEFAULT_CURRENCY)

    def test_void_loan_failure_raises_exception(self, bank_instance):
        # Setup: Create a loan manually (bypassing normal grant_loan to simulate broken link)
        loan_id = "loan_broken_link"

        # Manually insert _Loan into LoanManager
        bank_instance.loan_manager._loans[loan_id] = _Loan(
            loan_id=loan_id,
            borrower_id=999,
            principal=1000.0,
            remaining_balance=1000.0,
            annual_interest_rate=0.05,
            term_ticks=50,
            start_tick=0,
            origination_tick=0,
            created_deposit_id="non_existent_deposit_id"
        )

        with pytest.raises(LoanRollbackError):
            bank_instance.void_loan(loan_id)

        # Verify loan was NOT deleted (Atomic Rollback)
        assert loan_id in bank_instance.loan_manager._loans

    def test_loan_default_emits_event(self, bank_instance, mock_event_bus):
        borrower_id = 101

        # 1. Setup Defaulting Loan
        profile = BorrowerProfileDTO(borrower_id=borrower_id, gross_income=1000.0, existing_debt_payments=0.0, collateral_value=0.0, existing_assets=0.0)
        bank_instance.grant_loan(borrower_id, 1000.0, 0.05, borrower_profile=profile)

        # Mock Agent that fails to pay
        mock_borrower = MagicMock(spec=IFinancialAgent)
        mock_borrower.id = borrower_id
        # Force payment failure via assets check inside Bank (legacy path fallback) or just let callback fail
        # Bank.run_tick uses callback. If callback returns False, default happens.
        # Callback returns False if we simulate it via agents_dict

        # We need to ensure Bank.run_tick's payment_callback returns False.
        # It checks self.settlement_system (None in test) -> fallback.
        # Fallback checks IFinancialAgent.get_balance (New)
        mock_borrower.get_balance.return_value = 0.0 # Insufficient funds

        agents = {borrower_id: mock_borrower}

        # 2. Run Tick
        bank_instance.run_tick(agents, current_tick=10)

        # 3. Assert Event Published
        mock_event_bus.publish.assert_called()

        # Verify content of event
        call_args = mock_event_bus.publish.call_args
        event = call_args[0][0]

        assert event["event_type"] == "LOAN_DEFAULTED"
        assert event["agent_id"] == borrower_id
        assert event["defaulted_amount"] > 0
        assert event["creditor_id"] == bank_instance.id

    def test_loan_default_no_credit_destruction_transaction(self, bank_instance, mock_event_bus):
        # Regression Test: Ensure default does NOT destroy M2 (credit_destruction)
        borrower_id = 101
        profile = BorrowerProfileDTO(borrower_id=borrower_id, gross_income=1000.0, existing_debt_payments=0.0, collateral_value=0.0, existing_assets=0.0)
        bank_instance.grant_loan(borrower_id, 1000.0, 0.05, borrower_profile=profile)

        mock_borrower = MagicMock(spec=IFinancialAgent)
        mock_borrower.id = borrower_id
        mock_borrower.get_balance.return_value = 0.0 # Force default

        agents = {borrower_id: mock_borrower}
        transactions = bank_instance.run_tick(agents, current_tick=10)

        # Assert no credit_destruction tx
        destruction_txs = [tx for tx in transactions if tx.transaction_type == "credit_destruction"]
        assert len(destruction_txs) == 0, "Loan default should not trigger M2 destruction (credit_destruction transaction)."
