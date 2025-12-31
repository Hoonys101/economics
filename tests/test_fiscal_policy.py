
import pytest
from unittest.mock import MagicMock, Mock
from simulation.agents.government import Government
from simulation.core_agents import Household
from simulation.bank import Bank, Loan

class MockConfig:
    TAX_BRACKETS = [
        (1.5, 0.0),
        (5.0, 0.15),
        (float('inf'), 0.40)
    ]
    INCOME_TAX_RATE = 0.1
    ANNUAL_WEALTH_TAX_RATE = 0.02
    TICKS_PER_YEAR = 100
    WEALTH_TAX_THRESHOLD = 1000.0
    UNEMPLOYMENT_BENEFIT_RATIO = 0.8
    STIMULUS_TRIGGER_GDP_DROP = -0.05
    HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
    GOODS_INITIAL_PRICE = {"basic_food": 5.0}
    CREDIT_RECOVERY_TICKS = 100
    BANKRUPTCY_XP_PENALTY = 0.2
    TICKS_PER_YEAR = 100

def test_progressive_tax_calculation():
    gov = Government(id=1, config_module=MockConfig())
    survival_cost = 10.0

    # Case 1: Low Income (Under 1.5 * 10 = 15) -> 0%
    tax = gov.calculate_income_tax(10.0, survival_cost)
    assert tax == 0.0

    # Case 2: Middle Class (Between 15 and 50)
    # Income 40. First 15 is free. Remaining 25 is taxed at 15%.
    # 25 * 0.15 = 3.75
    tax = gov.calculate_income_tax(40.0, survival_cost)
    assert tax == pytest.approx(3.75)

    # Case 3: High Income (Over 50)
    # Income 100.
    # 0-15: 0
    # 15-50 (35 width): 35 * 0.15 = 5.25
    # 50-100 (50 width): 50 * 0.40 = 20.0
    # Total = 25.25
    tax = gov.calculate_income_tax(100.0, survival_cost)
    assert tax == pytest.approx(25.25)

def test_wealth_tax_collection():
    gov = Government(id=1, config_module=MockConfig())
    gov.collect_tax = MagicMock()

    rich_agent = MagicMock()
    rich_agent.id = 10
    rich_agent.assets = 2000.0 # Threshold 1000
    rich_agent.is_active = True
    rich_agent.shares_owned = {}
    rich_agent.needs = {} # Identify as household
    rich_agent.is_employed = True

    poor_agent = MagicMock()
    poor_agent.id = 11
    poor_agent.assets = 500.0
    poor_agent.is_active = True
    poor_agent.shares_owned = {}
    poor_agent.needs = {}
    poor_agent.is_employed = True

    market_data = {}

    gov.run_welfare_check([rich_agent, poor_agent], market_data, current_tick=1)

    # Wealth Tax: (2000 - 1000) * (0.02 / 100) = 1000 * 0.0002 = 0.2
    expected_tax = 0.2

    # Check if rich agent was taxed
    assert rich_agent.assets == 2000.0 - expected_tax
    gov.collect_tax.assert_called_with(expected_tax, "wealth_tax", 10, 1)

    # Check if poor agent was NOT taxed
    assert poor_agent.assets == 500.0

def test_unemployment_benefit():
    gov = Government(id=1, config_module=MockConfig())
    gov.provide_subsidy = MagicMock()
    gov.assets = 10000.0

    unemployed = MagicMock()
    unemployed.id = 20
    unemployed.is_employed = False
    unemployed.is_active = True
    unemployed.needs = {}
    unemployed.assets = 0.0

    market_data = {"goods_market": {"basic_food_current_sell_price": 5.0}}
    # Survival Cost = max(5.0 * 1.0, 10.0) = 10.0
    # Benefit = 10.0 * 0.8 = 8.0

    gov.run_welfare_check([unemployed], market_data, current_tick=1)

    gov.provide_subsidy.assert_called_with(unemployed, 8.0, 1)

def test_stimulus_trigger():
    gov = Government(id=1, config_module=MockConfig())
    gov.provide_subsidy = MagicMock()
    gov.assets = 10000.0

    agent = MagicMock()
    agent.id = 30
    agent.is_active = True
    agent.is_employed = True
    agent.needs = {} # Household
    agent.assets = 500.0 # Set explicit assets to avoid comparison error

    # Fill history with high GDP
    gov.gdp_history = [1000.0] * 10

    # Current GDP drops to 900 (10% drop, trigger is 5%)
    market_data = {
        "total_production": 900.0,
        "goods_market": {"basic_food_current_sell_price": 10.0}
    }

    gov.run_welfare_check([agent], market_data, current_tick=1)

    # Survival Cost = 10.0. Stimulus = 5 * 10.0 = 50.0
    gov.provide_subsidy.assert_called_with(agent, 50.0, 1)

def test_bank_process_default():
    bank = Bank(id=100, initial_assets=10000.0, config_module=MockConfig())

    loan = Loan(borrower_id=1, principal=100.0, remaining_balance=100.0, annual_interest_rate=0.05, term_ticks=50, start_tick=0)

    agent = MagicMock()
    agent.id = 1
    agent.shares_owned = {1: 10}
    agent.education_xp = 10.0
    agent.credit_frozen_until_tick = 0

    current_tick = 50
    bank.process_default(agent, loan, current_tick)

    # 1. Shares confiscated
    assert len(agent.shares_owned) == 0

    # 2. Loan forgiven
    assert loan.remaining_balance == 0.0

    # 3. XP Penalty
    # 10.0 * (1 - 0.2) = 8.0
    assert agent.education_xp == 8.0

    # 4. Credit Jail
    # 50 + 100 = 150
    assert agent.credit_frozen_until_tick == 150
