import pytest
from unittest.mock import MagicMock
from modules.system.registry import OriginType
import config
from simulation.finance.api import ISettlementSystem, IMonetaryAuthority

def test_config_hot_swap():
    # 1. Read initial
    # We need a key that exists. Let's use INITIAL_MONEY_SUPPLY.
    initial = config.INITIAL_MONEY_SUPPLY

    # 2. Update Registry
    config.registry.set("INITIAL_MONEY_SUPPLY", initial + 1, OriginType.USER)

    # 3. Verify Proxy
    assert config.INITIAL_MONEY_SUPPLY == initial + 1

    # Clean up
    config.registry.set("INITIAL_MONEY_SUPPLY", initial, OriginType.SYSTEM)

def test_strict_mock_enforcement():
    # 1. Basic Interface (ISettlementSystem)
    mock_settlement = MagicMock(spec=ISettlementSystem)

    # Should accept transfer
    mock_settlement.transfer(None, None, 100, "test")

    # Should REJECT mint_and_distribute (Admin method)
    with pytest.raises(AttributeError):
        mock_settlement.mint_and_distribute(1, 100)

    # 2. Admin Interface (IMonetaryAuthority)
    mock_authority = MagicMock(spec=IMonetaryAuthority)

    # Should accept mint_and_distribute
    mock_authority.mint_and_distribute(1, 100)

    # Should accept transfer (Inherited)
    mock_authority.transfer(None, None, 100, "test")

    # Should REJECT non-existent method
    with pytest.raises(AttributeError):
        mock_authority.make_it_rain()

def test_config_defaults_access():
    # Verify we can access EngineType (Enum) via config proxy
    assert config.EngineType is not None
    assert config.EngineType.AI_DRIVEN is not None
