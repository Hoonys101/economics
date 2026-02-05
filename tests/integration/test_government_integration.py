import pytest
from unittest.mock import MagicMock
from simulation.agents.government import Government
from modules.system.api import DEFAULT_CURRENCY

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.UNEMPLOYMENT_BENEFIT_RATIO = 0.5
    config.ANNUAL_WEALTH_TAX_RATE = 0.02
    config.TICKS_PER_YEAR = 100
    config.WEALTH_TAX_THRESHOLD = 1000.0
    config.STIMULUS_TRIGGER_GDP_DROP = -0.1
    config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
    config.GOODS_INITIAL_PRICE = {"basic_food": 10.0}
    # Add other attributes accessed by Government.__init__
    config.GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"
    config.INCOME_TAX_RATE = 0.1
    config.CORPORATE_TAX_RATE = 0.2
    config.CB_INFLATION_TARGET = 0.02
    config.ENABLE_FISCAL_STABILIZER = True
    return config

@pytest.fixture
def government(mock_config):
    gov = Government(id=1, initial_assets=100000.0, config_module=mock_config)
    gov.settlement_system = MagicMock()
    gov.settlement_system.transfer.return_value = True
    return gov

def test_government_execute_social_policy_tax_and_welfare(government):
    # Setup Agents
    # 1. Rich Agent (Taxable)
    rich_agent = MagicMock()
    rich_agent.id = 101
    rich_agent.is_active = True
    rich_agent.is_employed = True
    rich_agent.needs = {}
    rich_agent.assets = {DEFAULT_CURRENCY: 2000.0} # Net worth 2000. Taxable 1000 * 0.0002 = 0.2

    # 2. Poor Unemployed Agent (Welfare)
    poor_agent = MagicMock()
    poor_agent.id = 102
    poor_agent.is_active = True
    poor_agent.is_employed = False
    poor_agent.needs = {}
    poor_agent.assets = {DEFAULT_CURRENCY: 100.0}

    agents = [rich_agent, poor_agent]

    market_data = {
        "goods_market": {"basic_food_current_sell_price": 20.0},
        "total_production": 1000.0
    }

    # Execution
    government.run_welfare_check(agents, market_data, 100)

    # Verification - Tax
    # Expect transfer from rich_agent to gov
    # Amount: 0.2
    # Check calls to settlement_system.transfer

    transfer_calls = government.settlement_system.transfer.call_args_list

    # We expect 2 transfers: 1 tax, 1 welfare
    # Note: Order depends on execute_social_policy implementation (Tax first, then Welfare)
    assert len(transfer_calls) == 2

    # Check Tax Call
    args0, kwargs0 = transfer_calls[0]
    # self.settlement_system.transfer(req.payer, self, req.amount, req.memo, currency=req.currency)

    assert args0[0] == rich_agent
    assert args0[1] == government
    assert args0[2] == 0.2
    assert args0[3] == "wealth_tax"

    # Check Welfare Call
    # Benefit = 20.0 (survival) * 0.5 = 10.0
    args1, kwargs1 = transfer_calls[1]

    assert args1[0] == government
    assert args1[1] == poor_agent
    assert args1[2] == 10.0
    assert args1[3] == "welfare_support_unemployment"

    # Check Revenue Recorded
    assert government.tax_service.get_total_collected_this_tick() == 0.2

    # Check Expenditure Recorded
    # finalize_tick not called yet, but Manager tracks it.
    assert government.welfare_manager.get_spending_this_tick() == 10.0
