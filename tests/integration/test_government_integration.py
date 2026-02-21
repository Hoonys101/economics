import pytest
from unittest.mock import MagicMock
from simulation.agents.government import Government
from modules.system.api import DEFAULT_CURRENCY

class MockTaxableAgent:
    def __init__(self, id, balance):
        self.id = id
        self.balance_pennies = balance
        self.is_active = True
        self.is_employed = True
        self.needs = {}

    def deposit(self, amount, currency='USD'): pass
    def withdraw(self, amount, currency='USD'): pass
    def get_balance(self, currency='USD'): return self.balance_pennies
    def get_assets_by_currency(self): return {'USD': self.balance_pennies}

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.UNEMPLOYMENT_BENEFIT_RATIO = 0.5
    config.ANNUAL_WEALTH_TAX_RATE = 0.02
    config.TICKS_PER_YEAR = 100
    config.WEALTH_TAX_THRESHOLD = 100000 # 1000.00 dollars -> 100000 pennies
    config.STIMULUS_TRIGGER_GDP_DROP = -0.1
    config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
    config.GOODS_INITIAL_PRICE = {"basic_food": 10}
    # Add other attributes accessed by Government.__init__
    config.GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"
    config.INCOME_TAX_RATE = 0.1
    config.CORPORATE_TAX_RATE = 0.2
    config.CB_INFLATION_TARGET = 0.02
    config.ENABLE_FISCAL_STABILIZER = True
    return config

@pytest.fixture
def government(mock_config):
    gov = Government(id=1, initial_assets=100000, config_module=mock_config)
    gov.settlement_system = MagicMock()
    gov.settlement_system.transfer.return_value = True
    return gov

def test_government_execute_social_policy_tax_and_welfare(government):
    # Setup Agents
    # 1. Rich Agent (Taxable)
    rich_agent = MockTaxableAgent(id=101, balance=2000000)

    # 2. Poor Unemployed Agent (Welfare)
    # Using MockTaxableAgent for convenience, though only welfare checks matter
    poor_agent = MockTaxableAgent(id=102, balance=100)
    poor_agent.is_employed = False

    agents = [rich_agent, poor_agent]

    market_data = {
        "goods_market": {"basic_food_current_sell_price": 20},
        "total_production": 1000
    }

    # Execution
    government.run_welfare_check(agents, market_data, 100)

    # Verification - Tax
    # Expect transfer from rich_agent to gov
    # Threshold = 1000.0 * 100 = 100,000 pennies.
    # Taxable = 2,000,000 - 100,000 = 1,900,000.
    # Annual Rate = 0.02. Ticks = 100. Tick Rate = 0.0002.
    # Tax = 1,900,000 * 0.0002 = 380 pennies.
    # Check calls to settlement_system.transfer

    transfer_calls = government.settlement_system.transfer.call_args_list

    # We expect 2 transfers: 1 tax, 1 welfare
    # Note: Order depends on execute_social_policy implementation (Tax first, then Welfare)
    assert len(transfer_calls) == 2

    # Check Tax Call
    args0, kwargs0 = transfer_calls[0]
    # self.settlement_system.transfer(req.payer, self, req.amount, req.memo, currency=req.currency)

    assert args0[0].id == rich_agent.id
    assert args0[1].id == government.id
    assert args0[2] == 380
    assert args0[3] == "wealth_tax"

    # Check Welfare Call
    # Benefit = max(20, 1000) * 0.5 = 500 (Floor at 1000 pennies applied)
    args1, kwargs1 = transfer_calls[1]

    payer_val = args1[0]
    if hasattr(payer_val, 'id'):
        assert payer_val.id == government.id
    else:
        assert str(payer_val) == "GOVERNMENT" or str(payer_val) == str(government.id)

    assert args1[1].id == poor_agent.id
    assert args1[2] == 500
    assert args1[3] == "welfare_support_unemployment"

    # Check Revenue Recorded
    assert government.tax_service.get_total_collected_this_tick() == 380

    # Check Expenditure Recorded
    # finalize_tick not called yet, but Manager tracks it.
    assert government.welfare_manager.get_spending_this_tick() == 500
