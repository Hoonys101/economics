import pytest
from unittest.mock import MagicMock, patch
from typing import Any

from simulation.loan_market import LoanMarket
from simulation.bank import Bank
from modules.finance.api import MortgageApplicationDTO
from modules.finance.api import LoanDTO

class TestLoanMarketMortgage:
    @pytest.fixture
    def mock_bank(self):
        bank = MagicMock(spec=Bank)
        # Mock get_interest_rate
        bank.get_interest_rate.return_value = 0.05
        # Mock debt status
        bank.get_debt_status.return_value = {'loans': []}
        return bank

    @pytest.fixture
    def mock_config_module(self):
        config = MagicMock()
        config.DEFAULT_MORTGAGE_INTEREST_RATE = 0.05
        # Create nested regulations mock
        config.regulations = MagicMock()
        config.regulations.max_ltv_ratio = 0.8
        config.regulations.max_dti_ratio = 0.43
        return config

    @pytest.fixture
    def loan_market(self, mock_bank, mock_config_module):
        with patch("simulation.loan_market.logger"):
            return LoanMarket(
                market_id="test_market",
                bank=mock_bank,
                config_module=mock_config_module
            )

    def test_evaluate_mortgage_success(self, loan_market):
        app = MortgageApplicationDTO(
            applicant_id=1,
            requested_principal=8000000, # 80k pennies
            purpose="MORTGAGE",
            property_id=100,
            property_value=10000000, # 100k pennies
            applicant_monthly_income=500000, # 5k pennies
            existing_monthly_debt_payments=0,
            loan_term=360
        )
        assert loan_market.evaluate_mortgage_application(app) is True

    def test_evaluate_mortgage_fail_ltv(self, loan_market):
        app = MortgageApplicationDTO(
            applicant_id=1,
            requested_principal=9000000, # 90k pennies
            purpose="MORTGAGE",
            property_id=100,
            property_value=10000000,
            applicant_monthly_income=2000000,
            existing_monthly_debt_payments=0,
            loan_term=360
        )
        assert loan_market.evaluate_mortgage_application(app) is False

    def test_evaluate_mortgage_fail_dti(self, loan_market):
        # DTI limit 0.43
        app = MortgageApplicationDTO(
            applicant_id=1,
            requested_principal=10000000,
            purpose="MORTGAGE",
            property_id=100,
            property_value=20000000,
            applicant_monthly_income=100000,
            existing_monthly_debt_payments=0,
            loan_term=360
        )
        assert loan_market.evaluate_mortgage_application(app) is False

    def test_evaluate_mortgage_fail_dti_with_existing_debt(self, loan_market):
        app = MortgageApplicationDTO(
            applicant_id=1,
            requested_principal=5000000,
            purpose="MORTGAGE",
            property_id=100,
            property_value=20000000,
            applicant_monthly_income=100000,
            existing_monthly_debt_payments=20000, # Explicit existing debt
            loan_term=360
        )
        assert loan_market.evaluate_mortgage_application(app) is False

    def test_stage_mortgage_success(self, loan_market, mock_bank):
        app = MortgageApplicationDTO(
            applicant_id=1,
            requested_principal=8000000,
            purpose="MORTGAGE",
            property_id=100,
            property_value=10000000,
            applicant_monthly_income=500000,
            existing_monthly_debt_payments=0,
            loan_term=360
        )

        mock_bank.stage_loan.return_value = LoanDTO(
            loan_id="loan_123",
            borrower_id=1,
            principal_pennies=8000000,
            remaining_principal_pennies=8000000,
            interest_rate=0.05,
            origination_tick=0,
            due_tick=360,
            term_ticks=360,
            status="PENDING",
            lender_id=None
        )

        # Mock the loan existing in the bank for convert_staged_to_loan
        mock_loan = MagicMock()
        mock_loan.borrower_id = 1
        mock_loan.principal_pennies = 8000000
        mock_loan.remaining_principal_pennies = 8000000
        mock_loan.interest_rate = 0.05
        mock_loan.origination_tick = 0
        mock_loan.start_tick = 0
        mock_loan.term_ticks = 360
        # For DTO conversion, we need these attributes to be accessible
        mock_loan.due_tick = 360

        mock_bank.loans = {"loan_123": mock_loan}
        mock_bank.id = 999

        result = loan_market.stage_mortgage(app)
        assert result is not None
        assert result.loan_id == "loan_123"
        assert isinstance(result, LoanDTO)
        mock_bank.stage_loan.assert_called_once()

    def test_stage_mortgage_fail_eval(self, loan_market, mock_bank):
        app = MortgageApplicationDTO(
            applicant_id=1,
            requested_principal=9000000, # LTV Fail
            purpose="MORTGAGE",
            property_id=100,
            property_value=10000000,
            applicant_monthly_income=500000,
            existing_monthly_debt_payments=0,
            loan_term=360
        )

        result = loan_market.stage_mortgage(app)
        assert result is None
        mock_bank.stage_loan.assert_not_called()

    def test_end_to_end_dto_purity(self, loan_market, mock_bank):
        # Setup
        mock_loan = MagicMock()
        mock_loan.borrower_id = 1
        mock_loan.principal_pennies = 10000 # 100.00 dollars
        mock_loan.remaining_principal_pennies = 10000
        mock_loan.interest_rate = 0.05
        mock_loan.origination_tick = 0
        mock_loan.start_tick = 0
        mock_loan.term_ticks = 360
        mock_loan.due_tick = 360

        mock_bank.loans = {
            "loan_999": mock_loan
        }
        mock_bank.id = 1

        # Execute
        result = loan_market.convert_staged_to_loan("loan_999")

        # Verify
        assert isinstance(result, LoanDTO)
        assert result.loan_id == "loan_999"
        assert result.original_amount == 100.0
        assert result.outstanding_balance == 100.0
