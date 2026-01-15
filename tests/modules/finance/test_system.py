import pytest
from unittest.mock import Mock, MagicMock
from modules.finance.system import FinanceSystem

@pytest.fixture
def mock_config():
    config = Mock()
    config.STARTUP_GRACE_PERIOD_TICKS = 24
    config.ALTMAN_Z_SCORE_THRESHOLD = 1.81
    config.DEBT_RISK_PREMIUM_TIERS = {
        1.2: 0.05,
        0.9: 0.02,
        0.6: 0.005,
    }
    config.BOND_MATURITY_TICKS = 400
    config.QE_INTERVENTION_YIELD_THRESHOLD = 0.10
    config.BAILOUT_PENALTY_PREMIUM = 0.05
    config.BAILOUT_REPAYMENT_RATIO = 0.5
    return config

@pytest.fixture
def mock_government():
    gov = Mock()
    gov.assets = 10000.0
    gov.get_debt_to_gdp_ratio.return_value = 0.5
    return gov

@pytest.fixture
def mock_central_bank():
    cb = Mock()
    cb.get_interest_rate.return_value = 0.02
    return cb

@pytest.fixture
def mock_bank():
    bank = Mock()
    bank.assets = 100000.0
    return bank

@pytest.fixture
def finance_system(mock_government, mock_central_bank, mock_bank, mock_config):
    return FinanceSystem(mock_government, mock_central_bank, mock_bank, mock_config)

@pytest.fixture
def mock_firm():
    firm = Mock()
    firm.id = 1
    firm.age = 100
    firm.assets = 10000.0
    firm.cash_reserve = 5000.0
    firm.hr = Mock()
    firm.hr.get_total_wage_bill.return_value = 1000.0
    firm.finance = Mock()
    firm.finance.calculate_altman_z_score.return_value = 2.0
    return firm

def test_evaluate_solvency_startup_pass(finance_system, mock_firm):
    mock_firm.age = 10
    assert finance_system.evaluate_solvency(mock_firm, 100) is True

def test_evaluate_solvency_startup_fail(finance_system, mock_firm):
    mock_firm.age = 10
    mock_firm.cash_reserve = 1000.0
    assert finance_system.evaluate_solvency(mock_firm, 100) is False

def test_evaluate_solvency_established_pass(finance_system, mock_firm):
    assert finance_system.evaluate_solvency(mock_firm, 100) is True

def test_evaluate_solvency_established_fail(finance_system, mock_firm):
    mock_firm.finance.calculate_altman_z_score.return_value = 1.5
    assert finance_system.evaluate_solvency(mock_firm, 100) is False

def test_issue_treasury_bonds_market(finance_system, mock_government, mock_bank):
    amount = 1000.0
    initial_bank_assets = mock_bank.assets
    initial_gov_assets = mock_government.assets
    bonds = finance_system.issue_treasury_bonds(amount, 100)
    assert len(bonds) == 1
    assert mock_bank.assets == initial_bank_assets - amount
    assert mock_government.assets == initial_gov_assets + amount

def test_issue_treasury_bonds_qe(finance_system, mock_government, mock_central_bank):
    mock_government.get_debt_to_gdp_ratio.return_value = 1.5
    amount = 1000.0
    initial_gov_assets = mock_government.assets
    bonds = finance_system.issue_treasury_bonds(amount, 100)
    assert len(bonds) == 1
    mock_central_bank.purchase_bonds.assert_called_once()
    assert mock_government.assets == initial_gov_assets + amount

def test_issue_treasury_bonds_fail(finance_system, mock_government, mock_bank):
    amount = 200000.0
    bonds = finance_system.issue_treasury_bonds(amount, 100)
    assert len(bonds) == 0

def test_grant_bailout_loan(finance_system, mock_government, mock_firm, mock_config):
    amount = 5000.0
    initial_gov_assets = mock_government.assets
    loan = finance_system.grant_bailout_loan(mock_firm, amount)
    assert loan.firm_id == mock_firm.id
    assert loan.amount == amount
    assert loan.covenants["mandatory_repayment"] == mock_config.BAILOUT_REPAYMENT_RATIO
    assert mock_government.assets == initial_gov_assets - amount
    mock_firm.finance.add_liability.assert_called_once_with(amount, loan.interest_rate)
