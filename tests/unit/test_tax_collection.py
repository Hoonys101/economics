import pytest
from unittest.mock import MagicMock
from typing import Any, Optional, Dict
from simulation.agents.government import Government
from modules.finance.api import TaxCollectionResult
from modules.system.api import DEFAULT_CURRENCY

# Mock classes
class MockConfig:
    TICKS_PER_YEAR = 100
    GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"
    INCOME_TAX_RATE = 0.1
    CORPORATE_TAX_RATE = 0.2
    TAX_MODE = "PROGRESSIVE"
    ANNUAL_WEALTH_TAX_RATE = 0.02
    WEALTH_TAX_THRESHOLD = 100000 # 1000 dollars in pennies
    GOODS_INITIAL_PRICE = {"basic_food": 10.0}
    HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
    UNEMPLOYMENT_BENEFIT_RATIO = 0.5
    STIMULUS_TRIGGER_GDP_DROP = -0.1

class MockAgent:
    def __init__(self, id, assets):
        self.id = id
        self._wallet = {DEFAULT_CURRENCY: assets}
        self.is_active = True
        self.is_employed = True
        self.needs = {"labor_need": 0}

    def get_balance(self, currency=DEFAULT_CURRENCY):
        return self._wallet.get(currency, 0)

    @property
    def balance_pennies(self) -> int:
        return int(self._wallet.get(DEFAULT_CURRENCY, 0))

    def deposit(self, amount_pennies: int, currency=DEFAULT_CURRENCY) -> None:
        self._deposit(amount_pennies, currency)

    def withdraw(self, amount_pennies: int, currency=DEFAULT_CURRENCY) -> None:
        self._withdraw(amount_pennies, currency)

    def _deposit(self, amount, currency=DEFAULT_CURRENCY):
        self._wallet[currency] = self._wallet.get(currency, 0) + amount

    def _withdraw(self, amount, currency=DEFAULT_CURRENCY):
        self._wallet[currency] = self._wallet.get(currency, 0) - amount

class MockSettlementSystem:
    def __init__(self):
        self.transfer_calls = []

    def transfer(self, debit_agent, credit_agent, amount, memo, **kwargs):
        self.transfer_calls.append({
            "debit": debit_agent.id,
            "credit": credit_agent.id,
            "amount": amount,
            "memo": memo
        })
        # Use IFinancialAgent methods
        currency = kwargs.get('currency', DEFAULT_CURRENCY)
        if debit_agent.get_balance(currency) >= amount:
            debit_agent._withdraw(amount, currency)
            credit_agent._deposit(amount, currency)
            return True
        return False

    def get_balance(self, agent_id, currency=DEFAULT_CURRENCY):
        return 0 # Not used in these specific tests as assertions check objects directly

def test_atomic_wealth_tax_collection_success():
    config = MockConfig()
    gov = Government(id="GOV", initial_assets=0, config_module=config)
    settlement = MockSettlementSystem()
    gov.settlement_system = settlement

    # Household with assets > threshold (1000 dollars = 100,000 pennies)
    # Assets = 200,000 pennies ($2000). Taxable = 100,000.
    # Rate per tick = 0.02 / 100 = 0.0002
    # Tax = 1000 * 0.0002 = 0.2 dollars = 20 pennies
    # Assets = 2000.00 -> 200000 pennies
    household = MockAgent(id="HH1", assets=200000)

    market_data = {"goods_market": {"basic_food_current_sell_price": 10.0}}

    txs = gov.run_welfare_check([household], market_data, current_tick=1)

    # Check assets transferred
    assert household.get_balance() == 200000 - 20
    assert gov.get_balance() == 20

    # Check stats
    assert gov.total_collected_tax[DEFAULT_CURRENCY] == 20
    assert gov.tax_revenue["wealth_tax"] == 20

    # Check transactions: NO transaction objects for tax should be returned
    tax_txs = [t for t in txs if t.transaction_type == "tax"]
    assert len(tax_txs) == 0

def test_atomic_wealth_tax_collection_insufficient_funds():
    config = MockConfig()
    gov = Government(id="GOV", initial_assets=0, config_module=config)
    settlement = MockSettlementSystem()
    gov.settlement_system = settlement

    # This scenario is hard to hit because logic is min(tax, assets).
    # So let's force a situation where transfer fails by mocking settlement to fail

    household = MockAgent(id="HH1", assets=200000)

    # Override settlement to always fail
    settlement.transfer = MagicMock(return_value=False)

    market_data = {"goods_market": {"basic_food_current_sell_price": 10.0}}

    gov.run_welfare_check([household], market_data, current_tick=1)

    # Assets unchanged
    assert household.get_balance() == 200000
    assert gov.get_balance() == 0

    # Stats unchanged
    assert gov.total_collected_tax[DEFAULT_CURRENCY] == 0
    assert gov.tax_revenue.get("wealth_tax", 0) == 0
