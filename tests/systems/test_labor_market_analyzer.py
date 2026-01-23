import pytest
from unittest.mock import MagicMock
from simulation.systems.labor_market_analyzer import LaborMarketAnalyzer


@pytest.fixture
def analyzer():
    config = MagicMock()
    config.HOUSEHOLD_MIN_WAGE_DEMAND = 6.0
    return LaborMarketAnalyzer(config)


def test_update_market_history(analyzer):
    market_data = {"labor": {"avg_wage": 15.0}}
    analyzer.update_market_history(market_data)
    assert analyzer.market_wage_history[-1] == 15.0


def test_calculate_shadow_reservation_wage_increase(analyzer):
    # Employed agent, Wage < Shadow? No, usually Wage > Shadow pulls it up.
    # Logic: new = old * 0.95 + target * 0.05
    # target = max(current, shadow)

    agent = MagicMock()
    agent.is_employed = True
    agent.current_wage = 20.0
    agent.shadow_reservation_wage = 10.0

    # Target = 20.0
    # New = 10 * 0.95 + 20 * 0.05 = 9.5 + 1.0 = 10.5

    new_wage = analyzer.calculate_shadow_reservation_wage(agent, {})
    assert abs(new_wage - 10.5) < 0.001


def test_calculate_shadow_reservation_wage_decay(analyzer):
    # Unemployed agent
    # Logic: new = old * 0.98

    agent = MagicMock()
    agent.is_employed = False
    agent.shadow_reservation_wage = 10.0

    new_wage = analyzer.calculate_shadow_reservation_wage(agent, {})

    # 10 * 0.98 = 9.8
    assert abs(new_wage - 9.8) < 0.001


def test_calculate_shadow_reservation_wage_floor(analyzer):
    agent = MagicMock()
    agent.is_employed = False
    agent.shadow_reservation_wage = 6.05

    # Decay -> 6.05 * 0.98 = 5.929
    # Floor is 6.0

    new_wage = analyzer.calculate_shadow_reservation_wage(agent, {})
    assert new_wage == 6.0
