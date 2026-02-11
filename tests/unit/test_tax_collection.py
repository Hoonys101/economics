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
    WEALTH_TAX_THRESHOLD = 1000.0 # Dollars in config, converted to pennies by service
    GOODS_INITIAL_PRICE = {"basic_food": 10.0}
    HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
    UNEMPLOYMENT_BENEFIT_RATIO = 0.5
    STIMULUS_TRIGGER_GDP_DROP = -0.1

class MockAgent:
    def __init__(self, id, assets):
        self.id = id
        self._assets = assets
        self.is_active = True
        self.is_employed = True
        self.needs = {"labor_need": 0}

    @property
    def assets(self):
        return self._assets

    def _add_assets(self, amount):
        self._assets += amount

    def _sub_assets(self, amount):
        self._assets -= amount

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
        if debit_agent.assets >= amount:
            debit_agent._sub_assets(amount)
            if hasattr(credit_agent, 'deposit'):
                 credit_agent.deposit(amount)
            else:
                 credit_agent._add_assets(amount)
            return True
        return False

def test_atomic_wealth_tax_collection_success():
    config = MockConfig()
    gov = Government(id="GOV", initial_assets=0, config_module=config)
    settlement = MockSettlementSystem()
    gov.settlement_system = settlement

    # Household with assets > threshold (1000 dollars = 100,000 pennies)
    # Assets = 200,000 pennies ($2000). Taxable = 100,000.
    # Rate per tick = 0.02 / 100 = 0.0002
    # Tax = 100,000 * 0.0002 = 20 pennies
    household = MockAgent(id="HH1", assets=200000)

    market_data = {"goods_market": {"basic_food_current_sell_price": 10.0}}

    txs = gov.run_welfare_check([household], market_data, current_tick=1)

    # Check assets transferred
    assert household.assets == 200000 - 20
    assert gov.assets == 20

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
    assert household.assets == 200000
    assert gov.assets == 0

    # Stats unchanged
    assert gov.total_collected_tax[DEFAULT_CURRENCY] == 0
    assert gov.tax_revenue.get("wealth_tax", 0) == 0

def test_government_collect_tax_adapter_success():
    config = MockConfig()
    gov = Government(id="GOV", initial_assets=0, config_module=config)
    settlement = MockSettlementSystem()
    gov.settlement_system = settlement

    payer = MockAgent(id="PAYER", assets=100)
    amount = 10

    collected = gov.collect_tax(amount, "test_tax", payer, current_tick=1)

    assert collected['amount_collected'] == 10
    assert collected['success'] is True
    assert payer.assets == 90
    assert gov.assets == 10
    assert gov.total_collected_tax[DEFAULT_CURRENCY] == 10
    assert gov.tax_revenue["test_tax"] == 10

def test_government_collect_tax_adapter_failure():
    config = MockConfig()
    gov = Government(id="GOV", initial_assets=0, config_module=config)
    settlement = MockSettlementSystem()
    gov.settlement_system = settlement

    payer = MockAgent(id="PAYER", assets=5) # Less than 10
    amount = 10

    collected = gov.collect_tax(amount, "test_tax", payer, current_tick=1)

    assert collected['amount_collected'] == 0
    assert collected['success'] is False
    assert payer.assets == 5
    assert gov.assets == 0
    assert gov.total_collected_tax[DEFAULT_CURRENCY] == 0
    assert "test_tax" not in gov.tax_revenue
