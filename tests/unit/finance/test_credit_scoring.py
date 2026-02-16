import pytest
from unittest.mock import MagicMock
from modules.finance.credit_scoring import CreditScoringService
from modules.finance.api import BorrowerProfileDTO

class MockConfig:
    MAX_DEBT_TO_INCOME_RATIO = 0.40
    MAX_LOAN_TO_VALUE_RATIO = 0.80
    MAX_UNSECURED_LOAN_INCOME_MULTIPLIER = 3.0

@pytest.fixture
def scoring_service():
    return CreditScoringService(config_module=MockConfig())

def test_assess_approved(scoring_service):
    profile = BorrowerProfileDTO(
        gross_income=1000,
        existing_debt_payments=200,
        collateral_value=0,
    )
    # DTI = 200/1000 = 0.2 < 0.4. Approved.
    # Unsecured limit = 1000 * 3 = 3000.
    result = scoring_service.assess_creditworthiness(profile, 1000)
    assert result.is_approved is True
    assert result.max_loan_amount == 1000

def test_assess_dti_fail(scoring_service):
    profile = BorrowerProfileDTO(
        gross_income=1000,
        existing_debt_payments=500, # DTI 0.5 > 0.4
        collateral_value=0,
    )
    result = scoring_service.assess_creditworthiness(profile, 1000)
    assert result.is_approved is False
    assert "DTI ratio" in result.reason

def test_assess_ltv_fail(scoring_service):
    profile = BorrowerProfileDTO(
        gross_income=1000,
        existing_debt_payments=100,
        collateral_value=1000,
    )
    # LTV = 900 / 1000 = 0.9 > 0.8
    result = scoring_service.assess_creditworthiness(profile, 900)
    assert result.is_approved is False
    assert "LTV ratio" in result.reason

def test_assess_unsecured_cap_fail(scoring_service):
    profile = BorrowerProfileDTO(
        gross_income=100,
        existing_debt_payments=0,
        collateral_value=0,
    )
    # Cap = 100 * 3 = 300.
    result = scoring_service.assess_creditworthiness(profile, 400)
    assert result.is_approved is False
    assert "unsecured limit" in result.reason

def test_zero_income_fail(scoring_service):
    profile = BorrowerProfileDTO(
        gross_income=0,
        existing_debt_payments=0,
        collateral_value=0,
    )
    result = scoring_service.assess_creditworthiness(profile, 100)
    assert result.is_approved is False
    # Fails due to unsecured limit (Income * Multiplier = 0)
    assert "unsecured limit" in result.reason
