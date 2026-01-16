import pytest
from unittest.mock import Mock, MagicMock
from modules.finance.system import FinanceSystem
from modules.finance.api import InsufficientFundsError

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
    config.TICKS_PER_YEAR = 48
    return config

# Define simple stub classes for entity behavior
class StubGovernment:
    def __init__(self, assets=10000.0):
        self.assets = assets
        self.debt_to_gdp_ratio = 0.5
    def get_debt_to_gdp_ratio(self):
        return self.debt_to_gdp_ratio
    def deposit(self, amount): self.assets += amount
    def withdraw(self, amount):
        if self.assets < amount:
            raise InsufficientFundsError()
        self.assets -= amount

class StubCentralBank:
    def __init__(self, cash=50000.0):
        self.assets = {'cash': cash, 'bonds': []}
        self.base_rate = 0.02
    def get_base_rate(self):
        return self.base_rate
    def purchase_bonds(self, bond):
        self.assets['bonds'].append(bond)
    def deposit(self, amount): self.assets['cash'] += amount
    def withdraw(self, amount):
        if self.assets['cash'] < amount:
            raise InsufficientFundsError()
        self.assets['cash'] -= amount

class StubBank:
    def __init__(self, assets=100000.0):
        self.assets = assets
    def deposit(self, amount): self.assets += amount
    def withdraw(self, amount):
        if self.assets < amount:
            raise InsufficientFundsError()
        self.assets -= amount

@pytest.fixture
def mock_government():
    return StubGovernment()

@pytest.fixture
def mock_central_bank():
    return StubCentralBank()

@pytest.fixture
def mock_bank():
    return StubBank()

@pytest.fixture
def finance_system(mock_government, mock_central_bank, mock_bank, mock_config):
    return FinanceSystem(mock_government, mock_central_bank, mock_bank, mock_config)

class StubFirm:
    def __init__(self):
        self.id = 1
        self.age = 100
        self.assets = 10000.0
        self.cash_reserve = 5000.0
        self.hr = Mock()
        self.hr.get_total_wage_bill.return_value = 1000.0
        self.finance = MagicMock()
        self.finance.calculate_altman_z_score.return_value = 2.0
        self.has_bailout_loan = False
    def deposit(self, amount): self.cash_reserve += amount
    def withdraw(self, amount):
        if self.cash_reserve < amount:
            raise InsufficientFundsError()
        self.cash_reserve -= amount

@pytest.fixture
def mock_firm():
    return StubFirm()

def test_evaluate_solvency_startup_pass(finance_system, mock_firm):
    mock_firm.age = 10
    # Fix: Required runway is 3 * (1000 * 4) = 12000. Set cash reserve to match.
    mock_firm.cash_reserve = 12000.0
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
    mock_government.debt_to_gdp_ratio = 1.5
    # Fix: The yield rate (base + risk premium) must exceed the QE threshold.
    # Original: 0.02 (base) + 0.05 (risk) = 0.07 <= 0.10 (QE threshold) -> No QE
    # New: 0.06 (base) + 0.05 (risk) = 0.11 > 0.10 (QE threshold) -> QE triggered
    mock_central_bank.base_rate = 0.06
    amount = 1000.0
    initial_gov_assets = mock_government.assets
    initial_cb_cash = mock_central_bank.assets['cash']
    bonds = finance_system.issue_treasury_bonds(amount, 100)
    assert len(bonds) == 1
    assert len(mock_central_bank.assets['bonds']) == 1
    assert mock_government.assets == initial_gov_assets + amount
    assert mock_central_bank.assets['cash'] == initial_cb_cash - amount

def test_issue_treasury_bonds_fail(finance_system, mock_government, mock_bank):
    amount = 200000.0 # More than the bank's assets
    bonds = finance_system.issue_treasury_bonds(amount, 100)
    assert len(bonds) == 0

def test_bailout_fails_with_insufficient_government_funds(finance_system, mock_government, mock_firm):
    """Verify that a bailout loan is not granted if the government cannot afford it."""
    mock_government.assets = 100.0  # Not enough for the bailout
    amount = 500.0
    initial_gov_assets = mock_government.assets
    initial_firm_cash = mock_firm.cash_reserve

    loan = finance_system.grant_bailout_loan(mock_firm, amount)

    assert loan is None
    # Assert that no funds were moved
    assert mock_government.assets == initial_gov_assets
    assert mock_firm.cash_reserve == initial_firm_cash
    assert not mock_firm.has_bailout_loan

def test_grant_bailout_loan(finance_system, mock_government, mock_firm, mock_config):
    amount = 5000.0
    initial_gov_assets = mock_government.assets
    initial_firm_cash = mock_firm.cash_reserve
    loan = finance_system.grant_bailout_loan(mock_firm, amount)
    assert loan.firm_id == mock_firm.id
    assert loan.amount == amount
    assert loan.covenants.mandatory_repayment == mock_config.BAILOUT_REPAYMENT_RATIO
    assert mock_government.assets == initial_gov_assets - amount
    assert mock_firm.cash_reserve == initial_firm_cash + amount
    mock_firm.finance.add_liability.assert_called_once_with(amount, loan.interest_rate)

def test_service_debt_central_bank_repayment(finance_system, mock_government, mock_central_bank, mock_config):
    """
    Verify that when a bond held by the Central Bank matures, the repayment
    is correctly credited to the Central Bank's assets, preventing the
    "money destruction" bug.
    """
    # 1. Setup: Issue a bond that will be bought by the Central Bank via QE
    mock_government.debt_to_gdp_ratio = 1.5
    mock_central_bank.base_rate = 0.06
    mock_central_bank.assets = {"bonds": [], "cash": 10000.0}

    amount = 1000.0
    issue_tick = 100
    bonds = finance_system.issue_treasury_bonds(amount, issue_tick)
    bond = bonds[0]

    # 2. Action: Service the debt at the bond's maturity date
    maturity_date = bond.maturity_date
    initial_gov_assets = mock_government.assets
    initial_cb_cash = mock_central_bank.assets["cash"]

    finance_system.service_debt(maturity_date)

    # 3. Assertion: Verify the money was transferred correctly
    bond_lifetime_years = mock_config.BOND_MATURITY_TICKS / mock_config.TICKS_PER_YEAR
    interest = amount * bond.yield_rate * bond_lifetime_years
    total_repayment = amount + interest

    assert mock_government.assets == initial_gov_assets - total_repayment
    assert mock_central_bank.assets["cash"] == initial_cb_cash + total_repayment
    assert bond not in finance_system.outstanding_bonds
    assert bond not in mock_central_bank.assets["bonds"]
