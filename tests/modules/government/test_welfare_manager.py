import pytest
from unittest.mock import MagicMock
from modules.government.welfare.manager import WelfareManager
from modules.government.dtos import WelfareResultDTO, BailoutResultDTO
from simulation.dtos.api import MarketSnapshotDTO
from simulation.factories.golden_agents import create_golden_agent

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.UNEMPLOYMENT_BENEFIT_RATIO = 0.5
    config.STIMULUS_TRIGGER_GDP_DROP = -0.1
    config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
    # Config values might be float if they are prices, but here it's 10.0.
    # If WelfareManager converts it: "val = goods_market['basic_food_current_sell_price'] ... round_to_pennies(val * 100)"
    config.GOODS_INITIAL_PRICE = {"basic_food": 10.0}
    return config

@pytest.fixture
def welfare_manager(mock_config):
    return WelfareManager(mock_config)

@pytest.fixture
def golden_agent():
    # ID 101, unemployed, active
    agent = create_golden_agent(agent_id=101, assets_pennies=0, is_employed=False)
    # Needs are already {}, is_active is True
    return agent

@pytest.fixture
def market_data():
    return MarketSnapshotDTO(
        tick=100,
        market_signals={},
        market_data={
            "goods_market": {"basic_food_current_sell_price": 20.0},
            "total_production": 1000.0
        }
    )

def test_run_welfare_check_unemployment(welfare_manager, golden_agent, market_data):
    # Setup
    agents = [golden_agent]
    gdp_history = [1000.0] * 10

    # Execution
    result = welfare_manager.run_welfare_check(agents, market_data, 100, gdp_history)

    # Verification
    assert isinstance(result, WelfareResultDTO)
    assert len(result.payment_requests) == 1
    req = result.payment_requests[0]
    assert req.payee == golden_agent
    assert req.memo == "welfare_support_unemployment"

    # Calculation check: survival_cost = 20.0 * 1.0 = 20.0 -> 2000 pennies
    # benefit = 2000 * 0.5 = 1000 pennies
    assert req.amount == 1000
    assert welfare_manager.get_spending_this_tick() == 1000

def test_run_welfare_check_stimulus(welfare_manager, golden_agent, market_data):
    # Setup
    golden_agent.is_employed = True
    # For stimulus, any active household (which golden_agent is) gets it if trigger hits.

    agents = [golden_agent]

    # Trigger drop
    # Past GDP was 2000, current 1000. Drop 50%. Threshold -0.1 (10%).
    gdp_history = [2000.0] * 10

    # Execution
    result = welfare_manager.run_welfare_check(agents, market_data, 100, gdp_history)

    # Verification
    # Should have stimulus request
    assert len(result.payment_requests) == 1
    req = result.payment_requests[0]
    assert req.memo == "welfare_support_stimulus"

    # Calculation: survival_cost = 20.0 -> 2000 pennies.
    # Stimulus = 5 * survival = 10000 pennies.
    assert req.amount == 10000

def test_provide_firm_bailout(welfare_manager):
    # Firm ID is int, not agent object, for payee?
    # WelfareManager.provide_firm_bailout takes firm: IAgent.
    # Returns PaymentRequestDTO.payee as firm.id or firm?
    # Code: payee=firm.id

    firm = MagicMock()
    firm.id = 501

    # Solvent
    result = welfare_manager.provide_firm_bailout(firm, 5000, 100, is_solvent=True)
    assert isinstance(result, BailoutResultDTO)
    assert result.payment_request.amount == 5000
    assert result.payment_request.payee == 501
    assert result.loan_request.amount == 5000

    # Insolvent
    result_fail = welfare_manager.provide_firm_bailout(firm, 5000, 100, is_solvent=False)
    assert result_fail is None

def test_run_welfare_check_with_firm(welfare_manager, golden_agent, market_data):
    # Setup Firm: Should NOT be a welfare recipient
    firm = MagicMock()
    firm.id = 501
    firm.is_active = True
    # firm does NOT implement IWelfareRecipient (no 'is_employed', 'needs')
    # So it should be filtered out.

    agents = [golden_agent, firm]
    gdp_history = [1000.0] * 10

    # Execution
    result = welfare_manager.run_welfare_check(agents, market_data, 100, gdp_history)

    # Verification
    # Only golden_agent should be processed.
    assert len(result.payment_requests) == 1
    assert result.payment_requests[0].payee == golden_agent
