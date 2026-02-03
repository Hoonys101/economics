import pytest
from unittest.mock import MagicMock, patch
from typing import Any

from simulation.loan_market import LoanMarket
from simulation.bank import Bank
from modules.market.loan_api import MortgageApplicationRequestDTO
from modules.finance.api import LoanInfoDTO

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
        app = MortgageApplicationRequestDTO(
            applicant_id=1,
            requested_principal=80000.0,
            property_id=100,
            property_value=100000.0,
            applicant_monthly_income=5000.0, # 60k annual
            existing_monthly_debt_payments=0.0,
            loan_term=360
        )
        assert loan_market.evaluate_mortgage_application(app) is True

    def test_evaluate_mortgage_fail_ltv(self, loan_market):
        app = MortgageApplicationRequestDTO(
            applicant_id=1,
            requested_principal=90000.0, # 90% LTV
            property_id=100,
            property_value=100000.0,
            applicant_monthly_income=20000.0, # High income, so DTI is fine
            existing_monthly_debt_payments=0.0,
            loan_term=360
        )
        assert loan_market.evaluate_mortgage_application(app) is False

    def test_evaluate_mortgage_fail_dti(self, loan_market):
        # DTI limit 0.43
        # Income 1000.
        # Max obligation 430.
        # Loan principal 80000. Rate 5% (0.00416/mo). Term 360.
        # Payment approx 429.46
        # If existing debt is 10, total 439.46 > 430. Fail.

        # Let's use simpler numbers.
        # Principal 100,000. Pmt ~536.
        # Income 1000. DTI ~0.53 > 0.43. Fail.

        app = MortgageApplicationRequestDTO(
            applicant_id=1,
            requested_principal=100000.0,
            property_id=100,
            property_value=200000.0, # LTV 50% OK
            applicant_monthly_income=1000.0,
            existing_monthly_debt_payments=0.0,
            loan_term=360
        )
        assert loan_market.evaluate_mortgage_application(app) is False

    def test_evaluate_mortgage_fail_dti_with_existing_debt(self, loan_market):
        # Principal 50,000. Pmt ~268.
        # Income 1000.
        # Existing Debt Pmt 200.
        # Total 468. Ratio 0.468 > 0.43. Fail.

        app = MortgageApplicationRequestDTO(
            applicant_id=1,
            requested_principal=50000.0,
            property_id=100,
            property_value=200000.0,
            applicant_monthly_income=1000.0,
            existing_monthly_debt_payments=200.0, # Explicit existing debt
            loan_term=360
        )
        assert loan_market.evaluate_mortgage_application(app) is False

    def test_stage_mortgage_success(self, loan_market, mock_bank):
        app = MortgageApplicationRequestDTO(
            applicant_id=1,
            requested_principal=80000.0,
            property_id=100,
            property_value=100000.0,
            applicant_monthly_income=5000.0,
            existing_monthly_debt_payments=0.0,
            loan_term=360
        )

        mock_bank.stage_loan.return_value = {
            "loan_id": "loan_123",
            "original_amount": 80000.0
        }

        result = loan_market.stage_mortgage(app)
        assert result is not None
        assert result["loan_id"] == "loan_123"
        mock_bank.stage_loan.assert_called_once()

    def test_stage_mortgage_fail_eval(self, loan_market, mock_bank):
        app = MortgageApplicationRequestDTO(
            applicant_id=1,
            requested_principal=90000.0, # LTV Fail
            property_id=100,
            property_value=100000.0,
            applicant_monthly_income=5000.0,
            existing_monthly_debt_payments=0.0,
            loan_term=360
        )

        result = loan_market.stage_mortgage(app)
        assert result is None
        mock_bank.stage_loan.assert_not_called()
