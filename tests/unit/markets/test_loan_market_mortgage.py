import pytest
from unittest.mock import MagicMock, patch
from typing import Any

from simulation.loan_market import LoanMarket
from simulation.bank import Bank
from modules.market.housing_planner_api import MortgageApplicationDTO
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
        app = MortgageApplicationDTO(
            applicant_id=1,
            principal=80000.0,
            purpose="MORTGAGE",
            property_id=100,
            property_value=100000.0,
            applicant_income=60000.0,
            applicant_existing_debt=0.0,
            loan_term=360
        )
        assert loan_market.evaluate_mortgage_application(app) is True

    def test_evaluate_mortgage_fail_ltv(self, loan_market):
        app = MortgageApplicationDTO(
            applicant_id=1,
            principal=90000.0, # 90% LTV
            purpose="MORTGAGE",
            property_id=100,
            property_value=100000.0,
            applicant_income=200000.0, # High income, so DTI is fine
            applicant_existing_debt=0.0,
            loan_term=360
        )
        assert loan_market.evaluate_mortgage_application(app) is False

    def test_evaluate_mortgage_fail_dti(self, loan_market):
        app = MortgageApplicationDTO(
            applicant_id=1,
            principal=80000.0,
            purpose="MORTGAGE",
            property_id=100,
            property_value=100000.0,
            applicant_income=10000.0, # Low income
            applicant_existing_debt=0.0,
            loan_term=360
        )
        assert loan_market.evaluate_mortgage_application(app) is False

    def test_stage_mortgage_success(self, loan_market, mock_bank):
        app = MortgageApplicationDTO(
            applicant_id=1,
            principal=80000.0,
            purpose="MORTGAGE",
            property_id=100,
            property_value=100000.0,
            applicant_income=60000.0,
            applicant_existing_debt=0.0,
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
        app = MortgageApplicationDTO(
            applicant_id=1,
            principal=90000.0, # LTV Fail
            purpose="MORTGAGE",
            property_id=100,
            property_value=100000.0,
            applicant_income=60000.0,
            applicant_existing_debt=0.0,
            loan_term=360
        )

        result = loan_market.stage_mortgage(app)
        assert result is None
        mock_bank.stage_loan.assert_not_called()
