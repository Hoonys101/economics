import pytest
from unittest.mock import MagicMock, PropertyMock
from simulation.agents.central_bank import CentralBank
from modules.finance.monetary.api import (
    IMonetaryStrategy, MonetaryDecisionDTO, MonetaryRuleType, OMOActionType
)
from modules.system.api import DEFAULT_CURRENCY

@pytest.fixture
def mock_tracker():
    tracker = MagicMock()
    tracker.metrics = {"goods_price_index": [1.0, 1.02]}
    tracker.get_latest_indicators.return_value = {
        "gdp": 10000,
        "total_production": 100.0,
        "unemployment_rate": 5.0,
        "money_supply": 1000,
        "monetary_base": 200
    }
    return tracker

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.INITIAL_BASE_ANNUAL_RATE = 0.05
    config.CB_UPDATE_INTERVAL = 1
    config.CB_INFLATION_TARGET = 0.02
    config.TICKS_PER_YEAR = 100
    config.ENABLE_MONETARY_STABILIZER = True
    config.GOVERNMENT_POLICY_MODE = "TAYLOR_RULE"
    return config

@pytest.fixture
def mock_strategy_logic():
    strategy = MagicMock(spec=IMonetaryStrategy)
    type(strategy).rule_type = PropertyMock(return_value=MonetaryRuleType.TAYLOR_RULE)
    return strategy

def test_central_bank_initialization(mock_tracker, mock_config):
    cb = CentralBank(mock_tracker, mock_config)
    assert cb.base_rate == 0.05
    assert cb.monetary_policy.rule_type == MonetaryRuleType.TAYLOR_RULE

def test_central_bank_step_delegates_to_strategy(mock_tracker, mock_config, mock_strategy_logic):
    cb = CentralBank(mock_tracker, mock_config)
    cb.monetary_policy = mock_strategy_logic

    # Setup mock decision
    decision = MonetaryDecisionDTO(
        rule_type=MonetaryRuleType.TAYLOR_RULE,
        tick=10,
        target_interest_rate=0.06,
        omo_action=OMOActionType.NONE
    )
    mock_strategy_logic.calculate_decision.return_value = decision

    cb.step(10)

    # Verify calculate_decision called
    mock_strategy_logic.calculate_decision.assert_called_once()
    assert cb.base_rate == 0.06

def test_central_bank_omo_execution(mock_tracker, mock_config, mock_strategy_logic):
    cb = CentralBank(mock_tracker, mock_config)
    cb.monetary_policy = mock_strategy_logic

    # Mock Bond Market
    mock_market = MagicMock()
    mock_market.get_daily_avg_price.return_value = 1.0 # 1 Dollar
    cb.set_bond_market(mock_market)

    # Decision: BUY BONDS (QE)
    decision = MonetaryDecisionDTO(
        rule_type=MonetaryRuleType.FRIEDMAN_K_PERCENT,
        tick=10,
        target_interest_rate=0.05,
        omo_action=OMOActionType.BUY_BONDS,
        omo_amount_pennies=1000
    )
    mock_strategy_logic.calculate_decision.return_value = decision

    cb.step(10)

    # Verify Market Order Placed
    mock_market.place_order.assert_called_once()
    order = mock_market.place_order.call_args[0][0]
    assert order.side == "BUY"
    assert order.quantity == 10 # 1000 / 100
    assert order.agent_id == cb.id

def test_central_bank_snapshot_construction(mock_tracker, mock_config):
    cb = CentralBank(mock_tracker, mock_config)

    # Setup tracker data
    mock_tracker.get_latest_indicators.return_value = {
        "gdp": 5000, # Nominal
        "total_production": 100.0, # Real
        "unemployment_rate": 6.0,
        "money_supply": 2000,
        "monetary_base": 500,
        "velocity_of_money": 2.5
    }

    snapshot = cb._build_snapshot(10, mock_tracker.get_latest_indicators())

    assert snapshot.nominal_gdp == 5000
    assert snapshot.current_m2_supply == 2000
    assert snapshot.current_monetary_base == 500
    assert snapshot.unemployment_rate == 0.06 # 6.0 / 100
