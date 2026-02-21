import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
import os

if isinstance(TestClient, MagicMock) or (hasattr(TestClient, '__class__') and 'Mock' in TestClient.__class__.__name__):
    pytest.skip("fastapi is mocked, skipping server auth tests", allow_module_level=True)

# Add repo root to sys.path
sys.path.append(os.getcwd())

@pytest.fixture
def client_with_mocks():
    with patch("server.create_simulation") as mock_create_sim, \
         patch("server.DashboardService") as mock_dashboard_service, \
         patch("server.verify_god_mode_token") as mock_verify, \
         patch("server.config") as mock_config:

        mock_sim = MagicMock()
        mock_create_sim.return_value = mock_sim
        mock_dashboard_service.return_value = MagicMock()
        mock_config.GOD_MODE_TOKEN = "secret"

        from server import app
        client = TestClient(app)

        yield client, mock_verify

def test_websocket_auth_query_param(client_with_mocks):
    client, mock_verify = client_with_mocks
    mock_verify.return_value = True

    with client.websocket_connect("/ws/command?token=query_token") as websocket:
        pass

    # Check that verify_god_mode_token was called with "query_token"
    # Note: calls might be multiple if multiple connections, but here we just made one.
    # The lifespan startup might log stuff but shouldn't call verify_god_mode_token.

    # Filter calls to verify_god_mode_token
    # verify_god_mode_token(token, expected_token)

    # Check the last call
    args, _ = mock_verify.call_args
    assert args[0] == "query_token"

def test_websocket_auth_header(client_with_mocks):
    client, mock_verify = client_with_mocks
    mock_verify.return_value = True

    with client.websocket_connect("/ws/command", headers={"X-GOD-MODE-TOKEN": "header_token"}) as websocket:
        pass

    args, _ = mock_verify.call_args
    assert args[0] == "header_token"

def test_websocket_auth_failure(client_with_mocks):
    client, mock_verify = client_with_mocks
    mock_verify.return_value = False

    with pytest.raises(Exception) as excinfo:
        with client.websocket_connect("/ws/command?token=bad_token") as websocket:
            pass

    # WebSocket disconnect 403 or 1008
    # WebSocketDisconnect exception usually has a 'code' attribute
    from fastapi import WebSocketDisconnect
    assert isinstance(excinfo.value, WebSocketDisconnect)
    assert excinfo.value.code == 1008
