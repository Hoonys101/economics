import pytest
from unittest.mock import MagicMock, PropertyMock
from typing import List, Any
from modules.government.welfare.manager import WelfareManager
from modules.government.dtos import WelfareResultDTO, PaymentRequestDTO, BailoutResultDTO
from simulation.dtos.api import MarketSnapshotDTO
from modules.system.api import DEFAULT_CURRENCY

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.UNEMPLOYMENT_BENEFIT_RATIO = 0.5
    config.STIMULUS_TRIGGER_GDP_DROP = -0.1
    config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK = 1.0
    config.GOODS_INITIAL_PRICE = {"basic_food": 10.0}
    return config

@pytest.fixture
def welfare_manager(mock_config):
    return WelfareManager(mock_config)

@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.id = 101
    agent.is_active = True
    agent.is_employed = False
    agent.needs = {} # Marker for household
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

def test_run_welfare_check_unemployment(welfare_manager, mock_agent, market_data):
    # Setup
    agents = [mock_agent]
    gdp_history = [1000.0] * 10

    # Execution
    result = welfare_manager.run_welfare_check(agents, market_data, 100, gdp_history)

    # Verification
    assert isinstance(result, WelfareResultDTO)
    assert len(result.payment_requests) == 1
    req = result.payment_requests[0]
    assert req.payee == mock_agent
    assert req.memo == "welfare_support_unemployment"

    # Calculation check: survival_cost = 20.0 * 1.0 = 20.0
    # benefit = 20.0 * 0.5 = 10.0
    assert req.amount == 10.0
    assert welfare_manager.get_spending_this_tick() == 10.0

def test_run_welfare_check_stimulus(welfare_manager, mock_agent, market_data):
    # Setup
    mock_agent.is_employed = True # Employed agents get stimulus too? Logic: "active_households = [a for a in agents if hasattr(a, "is_employed") and getattr(a, "is_active", False)]"
    # Wait, employed or not, if they have "is_employed" attribute (households), they get stimulus?
    # Logic in manager: "active_households = [a for a in agents if hasattr(a, "is_employed") and getattr(a, "is_active", False)]"
    # Yes.

    agents = [mock_agent]

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

    # Calculation: survival_cost = 20.0. Stimulus = 5 * survival = 100.0.
    assert req.amount == 100.0

def test_provide_firm_bailout(welfare_manager):
    firm = MagicMock()
    firm.id = 501

    # Solvent
    result = welfare_manager.provide_firm_bailout(firm, 5000.0, 100, is_solvent=True)
    assert isinstance(result, BailoutResultDTO)
    assert result.payment_request.amount == 5000.0
    assert result.payment_request.payee == 501
    assert result.loan_request.amount == 5000.0

    # Insolvent
    result_fail = welfare_manager.provide_firm_bailout(firm, 5000.0, 100, is_solvent=False)
    assert result_fail is None
