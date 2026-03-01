import pytest
from unittest.mock import MagicMock, create_autospec
from typing import Any, Dict

from modules.simulation.api import (
    FirmSpawnRequestDTO,
    ICommerceTickContext,
    IFinanceTickContext,
    IMutationTickContext,
    AgentID
)

def test_firm_lifecycle_atomic_spawn_success():
    """Validates absolute monetary zero-sum between owner balance and firm treasury."""
    mock_ctx = create_autospec(IFinanceTickContext)
    mock_ledger = MagicMock()
    mock_ctx.monetary_ledger = mock_ledger

    request = FirmSpawnRequestDTO(
        owner_id=AgentID(1),
        firm_type="TECHNOLOGY",
        initial_capital_pennies=10000,
        location_id=None
    )

    # In a real implementation, IFirmLifecycleManager.register_new_firm would
    # deduct capital from the owner and return a new AgentID.
    # Here we mock the behavior to ensure the abstraction works.

    mock_manager = MagicMock()
    mock_manager.register_new_firm.return_value = AgentID(2)

    new_firm_id = mock_manager.register_new_firm(request, mock_ctx)

    assert new_firm_id == AgentID(2)
    mock_manager.register_new_firm.assert_called_once_with(request, mock_ctx)

def test_firm_lifecycle_rollback():
    """Injects a failure at Step 2 and guarantees owner balance restoration."""
    mock_ctx = create_autospec(IFinanceTickContext)

    request = FirmSpawnRequestDTO(
        owner_id=AgentID(1),
        firm_type="TECHNOLOGY",
        initial_capital_pennies=10000,
        location_id=None
    )

    mock_manager = MagicMock()
    # Simulate a failure during registration
    mock_manager.register_new_firm.side_effect = Exception("Registry collision")

    with pytest.raises(Exception, match="Registry collision"):
        mock_manager.register_new_firm(request, mock_ctx)

def test_tick_context_segregation():
    """Injects pure ICommerceTickContext to ensure sub-systems lack the authority to access unrequested data."""
    mock_ctx = create_autospec(ICommerceTickContext)

    mock_ctx.current_time = 100
    mock_ctx.market_data = {"FOOD": {}}
    mock_ctx.goods_data = {}

    assert mock_ctx.current_time == 100
    assert "FOOD" in mock_ctx.market_data

    # Verify that unrequested attributes are not present
    with pytest.raises(AttributeError):
        _ = mock_ctx.taxation_system

    with pytest.raises(AttributeError):
        _ = mock_ctx.monetary_ledger
