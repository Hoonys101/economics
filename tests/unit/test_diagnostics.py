import pytest
from unittest.mock import Mock
from simulation.world_state import WorldState
from modules.system.api import DEFAULT_CURRENCY

def test_get_total_system_money_diagnostics():
    # Mock WorldState dependencies
    from modules.simulation.dtos.api import MoneySupplyDTO

    mock_tracker = Mock()
    ws = WorldState(Mock(), Mock(), Mock(), Mock())
    ws.tracker = mock_tracker

    # Mock calculate_total_money returning MoneySupplyDTO
    # M2 is already aggregated in pennies
    ws.calculate_total_money = Mock(return_value=MoneySupplyDTO(
        total_m2_pennies=1550,
        system_debt_pennies=0
    ))

    total = ws.get_total_system_money_for_diagnostics(DEFAULT_CURRENCY)

    # Should return float representation of total_m2_pennies
    assert total == pytest.approx(1550.0)
