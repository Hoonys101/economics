import pytest
from unittest.mock import Mock
from simulation.world_state import WorldState
from modules.system.api import DEFAULT_CURRENCY

def test_get_total_system_money_diagnostics():
    # Mock WorldState dependencies
    mock_tracker = Mock()
    mock_exchange = Mock()
    mock_tracker.exchange_engine = mock_exchange

    ws = WorldState(Mock(), Mock(), Mock(), Mock())
    ws.tracker = mock_tracker

    # Mock calculate_total_money (we mock the method on the instance)
    ws.calculate_total_money = Mock(return_value={
        DEFAULT_CURRENCY: 1000.0,
        "EUR": 500.0
    })

    # Mock conversion: 1 EUR = 1.1 USD
    def convert(amount, from_c, to_c):
        if from_c == "EUR" and to_c == DEFAULT_CURRENCY:
            return amount * 1.1
        if from_c == DEFAULT_CURRENCY and to_c == DEFAULT_CURRENCY:
            return amount
        return 0.0

    mock_exchange.convert.side_effect = convert

    total = ws.get_total_system_money_for_diagnostics(DEFAULT_CURRENCY)

    # 1000 + 500*1.1 = 1550
    assert total == pytest.approx(1550.0)
