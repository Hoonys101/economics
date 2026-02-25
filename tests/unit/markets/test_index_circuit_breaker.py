import pytest
from unittest.mock import MagicMock
from modules.market.api import IndexCircuitBreakerConfigDTO
from simulation.markets.market_circuit_breaker import IndexCircuitBreaker

@pytest.fixture
def breaker_config():
    return IndexCircuitBreakerConfigDTO(
        threshold_level_1=0.08,
        threshold_level_2=0.15,
        threshold_level_3=0.20,
        halt_duration_level_1=10,
        halt_duration_level_2=20
    )

@pytest.fixture
def circuit_breaker(breaker_config):
    return IndexCircuitBreaker(config=breaker_config)

def test_initial_state(circuit_breaker):
    assert not circuit_breaker.is_active()

def test_happy_path_no_drop(circuit_breaker):
    circuit_breaker.set_reference_index(100.0)
    market_stats = {'market_index': 99.0} # 1% drop
    assert circuit_breaker.check_market_health(market_stats, current_tick=10) is True
    assert not circuit_breaker.is_active()

def test_level_1_trigger(circuit_breaker):
    circuit_breaker.set_reference_index(100.0)
    market_stats = {'market_index': 91.0} # 9% drop > 8%
    assert circuit_breaker.check_market_health(market_stats, current_tick=10) is False
    assert circuit_breaker.is_active()
    # Should halt for 10 ticks (10 + 10 = 20)

    # Check during halt
    assert circuit_breaker.check_market_health(market_stats, current_tick=15) is False
    assert circuit_breaker.is_active()

    # Check after halt duration
    assert circuit_breaker.check_market_health(market_stats, current_tick=20) is True
    assert not circuit_breaker.is_active()

def test_level_escalation(circuit_breaker):
    circuit_breaker.set_reference_index(100.0)

    # Trigger Level 1
    market_stats = {'market_index': 91.0} # 9% drop
    assert circuit_breaker.check_market_health(market_stats, current_tick=10) is False

    # Fast forward to resume
    assert circuit_breaker.check_market_health(market_stats, current_tick=20) is True

    # Trigger Level 2
    market_stats = {'market_index': 84.0} # 16% drop > 15%
    assert circuit_breaker.check_market_health(market_stats, current_tick=21) is False
    assert circuit_breaker.is_active()
    # Should halt for 20 ticks (21 + 20 = 41)

    # Check halt duration
    assert circuit_breaker.check_market_health(market_stats, current_tick=30) is False
    assert circuit_breaker.check_market_health(market_stats, current_tick=41) is True

def test_level_3_indefinite_halt(circuit_breaker):
    circuit_breaker.set_reference_index(100.0)
    market_stats = {'market_index': 75.0} # 25% drop > 20%
    assert circuit_breaker.check_market_health(market_stats, current_tick=10) is False
    assert circuit_breaker.is_active()

    # Check much later, still halted
    assert circuit_breaker.check_market_health(market_stats, current_tick=1000) is False
    assert circuit_breaker.is_active()

def test_reference_index_reset(circuit_breaker):
    circuit_breaker.set_reference_index(100.0)
    market_stats = {'market_index': 90.0} # 10% drop, triggers level 1
    circuit_breaker.check_market_health(market_stats, current_tick=10)
    assert circuit_breaker.is_active()

    # New session reset
    circuit_breaker.set_reference_index(200.0)
    assert not circuit_breaker.is_active()
    assert circuit_breaker._current_level == 0

    # Check relative to new index
    market_stats = {'market_index': 190.0} # 5% drop
    assert circuit_breaker.check_market_health(market_stats, current_tick=11) is True

def test_missing_index_fail_open(circuit_breaker):
    circuit_breaker.set_reference_index(100.0)
    market_stats = {} # Missing index
    assert circuit_breaker.check_market_health(market_stats, current_tick=10) is True

def test_zero_reference_index(circuit_breaker):
    circuit_breaker.set_reference_index(0.0)
    market_stats = {'market_index': 50.0}
    assert circuit_breaker.check_market_health(market_stats, current_tick=10) is True
