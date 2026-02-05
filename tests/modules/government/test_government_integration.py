import pytest
from unittest.mock import MagicMock
from simulation.agents.government import Government
from modules.government.dtos import WelfareResultDTO, PaymentRequestDTO, TaxCollectionResultDTO
from modules.system.api import DEFAULT_CURRENCY
from modules.government.constants import DEFAULT_TICKS_PER_YEAR

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.TICKS_PER_YEAR = 100
    config.ANNUAL_WEALTH_TAX_RATE = 0.01
    config.WEALTH_TAX_THRESHOLD = 1000.0
    config.UNEMPLOYMENT_BENEFIT_RATIO = 0.5
    config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
    config.GOODS_INITIAL_PRICE = {"basic_food": 10.0}
    config.STIMULUS_TRIGGER_GDP_DROP = -0.1
    return config

def test_execute_social_policy_integration(mock_config):
    # Setup Government
    gov = Government(id=1, initial_assets=10000.0, config_module=mock_config)
    gov.settlement_system = MagicMock()
    # Mock transfer to return True
    gov.settlement_system.transfer.return_value = True

    # Create Mock Agent conforming to IWelfareRecipient
    agent = MagicMock()
    agent.id = 101
    agent.is_active = True
    agent.is_employed = False
    agent.assets = {DEFAULT_CURRENCY: 500.0}
    # needs is not strictly required by WelfareManager anymore but good for complete mock
    agent.needs = {}

    agents = [agent]
    market_data = {
        "goods_market": {"basic_food_current_sell_price": 10.0},
        "total_production": 1000.0
    }

    # Pre-populate GDP history to avoid stimulus trigger
    gov.gdp_history = [1000.0] * 20

    # Execution
    gov.execute_social_policy(agents, market_data, current_tick=100)

    # Verification
    # 1. Tax: 500 < 1000 -> 0 tax.
    # 2. Welfare: Unemployed -> Benefit.
    # Survival cost = 10.0 * 1.0 = 10.0.
    # Benefit = 10.0 * 0.5 = 5.0.

    # Check settlement system calls
    # Expect transfer from Gov to Agent for Welfare
    gov.settlement_system.transfer.assert_called()

    # Find the welfare transfer call
    calls = gov.settlement_system.transfer.call_args_list
    welfare_call = None
    for call in calls:
        args, kwargs = call
        # signature: transfer(payer, payee, amount, memo, currency=...)
        if args[0] == gov and args[1] == agent:
            welfare_call = call
            break

    assert welfare_call is not None, "Welfare transfer not found"
    args, kwargs = welfare_call
    assert args[2] == 5.0
    assert args[3] == "welfare_support_unemployment"

def test_execute_social_policy_tax_and_welfare(mock_config):
    # Setup Government
    gov = Government(id=1, initial_assets=10000.0, config_module=mock_config)
    gov.settlement_system = MagicMock()
    gov.settlement_system.transfer.return_value = True

    # Rich Unemployed Agent
    agent = MagicMock()
    agent.id = 102
    agent.is_active = True
    agent.is_employed = False
    # Wealth = 2000. Threshold = 1000. Taxable = 1000.
    # Rate = 0.01 / 100 = 0.0001 per tick.
    # Tax = 1000 * 0.0001 = 0.1.
    agent.assets = {DEFAULT_CURRENCY: 2000.0}
    agent.needs = {}

    agents = [agent]
    market_data = {
        "goods_market": {"basic_food_current_sell_price": 10.0},
        "total_production": 1000.0
    }
    gov.gdp_history = [1000.0] * 20

    # Execution
    gov.execute_social_policy(agents, market_data, current_tick=100)

    # Verification
    # Check Tax Transfer (Agent -> Gov)
    # Check Welfare Transfer (Gov -> Agent)

    calls = gov.settlement_system.transfer.call_args_list

    # Tax Call
    tax_found = False
    for call in calls:
        args, kwargs = call
        if args[0] == agent and args[1] == gov:
            assert args[2] == 0.1
            assert args[3] == "wealth_tax"
            tax_found = True
    assert tax_found

    # Welfare Call
    welfare_found = False
    for call in calls:
        args, kwargs = call
        if args[0] == gov and args[1] == agent:
            assert args[2] == 5.0
            assert args[3] == "welfare_support_unemployment"
            welfare_found = True
    assert welfare_found
