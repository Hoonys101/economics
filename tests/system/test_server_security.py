import pytest
import logging
from unittest.mock import MagicMock, patch
from simulation.dtos.config_dtos import ServerConfigDTO
from modules.system.server import SimulationServer
from modules.system.server_bridge import CommandQueue, TelemetryExchange

def test_server_config_dto_defaults():
    """Verify ServerConfigDTO defaults to secure settings."""
    config = ServerConfigDTO(god_mode_token="test")
    assert config.host == "127.0.0.1"
    assert config.port == 8000
    assert config.god_mode_token == "test"

def test_server_binding_check_secure():
    """Verify SimulationServer accepts localhost binding without critical log."""
    config = ServerConfigDTO(host="127.0.0.1", port=8000, god_mode_token="test")
    cq = CommandQueue()
    te = TelemetryExchange()

    with patch("modules.system.server.logger") as mock_logger:
        server = SimulationServer(config, cq, te)
        # Should NOT log critical
        mock_logger.critical.assert_not_called()
        assert server.host == "127.0.0.1"

def test_server_binding_check_insecure():
    """Verify SimulationServer logs critical warning for non-localhost binding."""
    config = ServerConfigDTO(host="0.0.0.0", port=8000, god_mode_token="test")
    cq = CommandQueue()
    te = TelemetryExchange()

    with patch("modules.system.server.logger") as mock_logger:
        server = SimulationServer(config, cq, te)
        # Should log critical
        mock_logger.critical.assert_called_once()
        args, _ = mock_logger.critical.call_args
        assert "SECURITY ALERT" in args[0]
        assert "0.0.0.0" in args[0]

def test_server_properties_proxied():
    """Verify SimulationServer properties correctly proxy config values."""
    config = ServerConfigDTO(host="localhost", port=9000, god_mode_token="secret")
    cq = CommandQueue()
    te = TelemetryExchange()
    server = SimulationServer(config, cq, te)

    assert server.host == "localhost"
    assert server.port == 9000
    assert server.god_mode_token == "secret"
