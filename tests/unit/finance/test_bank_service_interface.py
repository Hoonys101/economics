import pytest
from unittest.mock import MagicMock, Mock
from typing import Optional, List
from modules.finance.api import (
    IBankService,
    LoanInfoDTO,
    DebtStatusDTO,
    LoanNotFoundError,
    LoanRepaymentError,
    IFinanceSystem
)
from simulation.bank import Bank
from modules.common.config_manager.api import ConfigManager
from simulation.models import Transaction

class TestBankServiceInterface:
    @pytest.fixture
    def mock_config_manager(self):
        config = MagicMock(spec=ConfigManager)
        config.get.side_effect = lambda key, default=None: default
        return config

    @pytest.fixture
    def mock_finance_system(self):
        return MagicMock(spec=IFinanceSystem)

    @pytest.fixture
    def bank(self, mock_config_manager, mock_finance_system):
        bank = Bank(id=1, initial_assets=1000000, config_manager=mock_config_manager)
        bank.set_finance_system(mock_finance_system)
        return bank

    def test_bank_methods_presence(self, bank):
        assert hasattr(bank, 'grant_loan')
        assert hasattr(bank, 'repay_loan')
        assert hasattr(bank, 'get_balance')
        assert hasattr(bank, 'get_debt_status')
        assert hasattr(bank, '_deposit')
        assert hasattr(bank, '_withdraw')

    def test_grant_loan(self, bank, mock_finance_system):
        borrower_id = "101"
        amount = 100000 # 1000.00
        interest_rate = 0.05

        # Setup Mock Response
        loan_dto = LoanInfoDTO(
            loan_id="loan_1",
            borrower_id=borrower_id,
            original_amount=amount,
            outstanding_balance=amount,
            interest_rate=interest_rate,
            origination_tick=0,
            due_tick=100,
            status="ACTIVE",
            term_ticks=360
        )
        tx = Transaction(
            buyer_id=bank.id,
            seller_id=borrower_id,
            item_id="credit_creation_loan_1",
            quantity=1.0,
            price=amount,
            market_id="finance",
            transaction_type="credit_creation",
            time=0
        )
        mock_finance_system.process_loan_application.return_value = (loan_dto, [tx])

        result = bank.grant_loan(borrower_id, amount, interest_rate)
        assert result is not None
        loan_info, transaction = result

        assert loan_info.borrower_id == borrower_id
        assert loan_info.original_amount == amount
        assert loan_info.outstanding_balance == amount
        assert loan_info.interest_rate == interest_rate
        assert loan_info.loan_id == "loan_1"

        # Transaction verification
        assert transaction is not None
        assert transaction.price == amount
        assert transaction.buyer_id == bank.id

    def test_repay_loan(self, bank):
        # repay_loan is currently not fully implemented in Bank to delegate to Engine for manual calls
        success = bank.repay_loan("loan_1", 20000)
        assert success is False

    def test_get_balance(self, bank, mock_finance_system):
        depositor_id = 202

        mock_finance_system.get_customer_balance.return_value = 50000 # 500.00

        balance = bank.get_customer_balance(depositor_id)
        assert balance == 50000

        mock_finance_system.get_customer_balance.assert_called_with(bank.id, depositor_id)

    def test_get_debt_status(self, bank, mock_finance_system):
        borrower_id = "303"

        loans = [
            LoanInfoDTO(
                loan_id="l1", borrower_id=borrower_id, original_amount=100000,
                outstanding_balance=100000, interest_rate=0.05, origination_tick=0, due_tick=100,
                status="ACTIVE", term_ticks=360
            ),
            LoanInfoDTO(
                loan_id="l2", borrower_id=borrower_id, original_amount=50000,
                outstanding_balance=50000, interest_rate=0.06, origination_tick=0, due_tick=100,
                status="ACTIVE", term_ticks=360
            )
        ]
        mock_finance_system.get_customer_debt_status.return_value = loans

        status = bank.get_debt_status(borrower_id)

        assert status.borrower_id == borrower_id
        assert status.total_outstanding_debt == 150000
        assert len(status.loans) == 2
        assert status.is_insolvent is False

    def test_interface_compliance_mypy(self):
        pass
