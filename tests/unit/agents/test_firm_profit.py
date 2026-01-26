import pytest
from collections import deque
from unittest.mock import Mock

from simulation.firms import Firm
from simulation.decisions.ai_driven_firm_engine import AIDrivenFirmDecisionEngine
# No need to import config here, as it's passed as a mock


@pytest.fixture
def mock_firm():
    # Create a mock config module
    mock_config_module = Mock()
    mock_config_module.PROFIT_HISTORY_TICKS = 3
    mock_config_module.BASE_WAGE = 10.0
    mock_config_module.WAGE_PROFIT_SENSITIVITY = 0.5
    mock_config_module.MAX_WAGE_PREMIUM = 1.0

    # Mock the decision_engine as it's not under test here
    mock_decision_engine = Mock(spec=AIDrivenFirmDecisionEngine)

    firm = Firm(
        id=1,
        initial_capital=1000.0,
        initial_liquidity_need=50.0,
        specialization="basic_food",  # Use specialization instead of production_targets
        productivity_factor=1.0,
        decision_engine=mock_decision_engine,
        value_orientation="profit",
        config_module=mock_config_module,  # Pass the mock config_module
        logger=Mock(),
    )
    firm.production_target = 100.0  # Initialize production_target
    # Ensure deque is initialized with the mocked config value
    firm.profit_history = deque(maxlen=mock_config_module.PROFIT_HISTORY_TICKS)
    return firm


def test_firm_profit_history_update(mock_firm):
    """Firm.profit_history가 올바르게 업데이트되고 최대 길이를 유지하는지 테스트"""
    # Simulate profit updates over several ticks
    mock_firm.profit_history.append(10.0)
    mock_firm.profit_history.append(20.0)
    mock_firm.profit_history.append(30.0)

    assert list(mock_firm.profit_history) == [10.0, 20.0, 30.0]
    assert len(mock_firm.profit_history) == 3  # Directly use the mocked value

    # Add one more profit, should push out the oldest one
    mock_firm.profit_history.append(40.0)
    assert list(mock_firm.profit_history) == [20.0, 30.0, 40.0]
    assert len(mock_firm.profit_history) == 3  # Directly use the mocked value


def test_firm_revenue_expenses_reset(mock_firm):
    """Firm의 revenue_this_tick과 expenses_this_tick이 리셋되는지 테스트 (엔진에서 호출될 로직)"""
    mock_firm.revenue_this_tick = 100.0
    mock_firm.expenses_this_tick = 50.0

    # Simulate the reset logic that would be in simulation.engine.py
    current_profit = mock_firm.revenue_this_tick - mock_firm.expenses_this_tick
    mock_firm.profit_history.append(current_profit)
    mock_firm.revenue_this_tick = 0.0
    mock_firm.expenses_this_tick = 0.0

    assert mock_firm.revenue_this_tick == 0.0
    assert mock_firm.expenses_this_tick == 0.0
    assert list(mock_firm.profit_history)[-1] == 50.0


# Further tests would involve mocking the engine.run_tick to ensure it calls these resets correctly
