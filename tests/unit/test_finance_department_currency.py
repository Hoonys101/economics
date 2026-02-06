import pytest
from unittest.mock import Mock, MagicMock
from simulation.components.finance_department import FinanceDepartment
from modules.finance.dtos import MoneyDTO
from modules.system.api import DEFAULT_CURRENCY
from modules.finance.api import InsufficientFundsError

class MockWallet:
    def __init__(self):
        self.balances = {DEFAULT_CURRENCY: 1000.0, "EUR": 500.0}

    def get_all_balances(self):
        return self.balances

    def get_balance(self, currency):
        return self.balances.get(currency, 0.0)

    def add(self, amount, currency, memo=""):
        self.balances[currency] = self.balances.get(currency, 0.0) + amount

    def subtract(self, amount, currency, memo=""):
        self.balances[currency] = self.balances.get(currency, 0.0) - amount

@pytest.fixture
def firm_mock():
    firm = Mock()
    firm.wallet = MockWallet()
    firm.id = 1
    firm.total_shares = 100
    firm.treasury_shares = 0
    firm.dividend_rate = 0.1
    firm.inventory = {}
    firm.capital_stock = 100.0
    firm.last_prices = {}
    firm.settlement_system = None
    firm.has_bailout_loan = False
    firm.total_debt = 0.0
    return firm

@pytest.fixture
def config_mock():
    config = Mock()
    config.profit_history_ticks = 10
    config.inventory_holding_cost_rate = 0.01
    config.firm_maintenance_fee = 10.0
    config.valuation_per_multiplier = 10.0
    config.bailout_repayment_ratio = 0.1
    return config

def test_multi_currency_balance(firm_mock, config_mock):
    finance = FinanceDepartment(firm_mock, config_mock)
    assert finance.get_balance(DEFAULT_CURRENCY) == 1000.0
    assert finance.get_balance("EUR") == 500.0

def test_deposit_withdraw(firm_mock, config_mock):
    finance = FinanceDepartment(firm_mock, config_mock)
    finance.deposit(100.0, "EUR")
    assert finance.get_balance("EUR") == 600.0

    finance.withdraw(50.0, "EUR")
    assert finance.get_balance("EUR") == 550.0

    with pytest.raises(InsufficientFundsError):
        finance.withdraw(1000.0, "EUR")

def test_valuation(firm_mock, config_mock):
    finance = FinanceDepartment(firm_mock, config_mock)
    market_context = {
        "exchange_rates": {DEFAULT_CURRENCY: 1.0, "EUR": 1.1},
        "benchmark_rates": {}
    }

    # 1000 USD + 500 EUR * 1.1 = 1000 + 550 = 1550 USD cash
    # Inventory 0
    # Capital Stock 100
    # Total Assets = 1650
    # Profit 0
    # Valuation = 1650

    val = finance.calculate_valuation(market_context)
    assert val['currency'] == DEFAULT_CURRENCY
    assert val['amount'] == pytest.approx(1650.0)

def test_generate_transactions_dividends(firm_mock, config_mock):
    finance = FinanceDepartment(firm_mock, config_mock)
    finance.current_profit = {DEFAULT_CURRENCY: 100.0, "EUR": 50.0}

    # Mock households
    h1 = Mock()
    h1.id = 101
    # TD-233 Fix: Mock get_stock_quantity instead of to_legacy_dict
    h1.portfolio.get_stock_quantity.side_effect = lambda fid: 50.0 if fid == 1 else 0.0

    market_context = {
        "exchange_rates": {DEFAULT_CURRENCY: 1.0, "EUR": 1.1},
        "benchmark_rates": {}
    }

    transactions = finance.process_profit_distribution([h1], Mock(), 1, market_context)

    # Expect dividend in USD: 100 * 0.1 = 10 total. H1 gets 5.
    # Expect dividend in EUR: 50 * 0.1 = 5 total. H1 gets 2.5.

    assert len(transactions) == 2
    usd_tx = next(t for t in transactions if t.currency == DEFAULT_CURRENCY)
    eur_tx = next(t for t in transactions if t.currency == "EUR")

    assert usd_tx.price == 5.0
    assert eur_tx.price == 2.5

def test_altman_z_score_multi_currency(firm_mock, config_mock):
    # TD-240 Verification
    finance = FinanceDepartment(firm_mock, config_mock)
    market_context = {
        "exchange_rates": {DEFAULT_CURRENCY: 1.0, "EUR": 1.2},
        "benchmark_rates": {}
    }

    # USD Balance: 1000.0
    # EUR Balance: 500.0 -> 600.0 USD
    # Total Cash: 1600.0 USD
    # Capital Stock: 100.0 USD
    # Inventory: 0.0
    # Total Assets = 1700.0

    # Working Capital = 1600.0
    # Retained Earnings = 0.0
    # Avg Profit = 0.0

    # x1 = 1600/1700 = 0.941176

    score = finance.calculate_altman_z_score(market_context)

    expected_x1 = 1600.0 / 1700.0
    expected_score = 1.2 * expected_x1

    assert score == pytest.approx(expected_score, abs=0.0001)
