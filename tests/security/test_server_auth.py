import pytest
from fastapi.testclient import TestClient
from server import app
from unittest.mock import patch, MagicMock
from fastapi import WebSocketDisconnect

if isinstance(TestClient, MagicMock) or (hasattr(TestClient, '__class__') and 'Mock' in TestClient.__class__.__name__):
    pytest.skip("fastapi is mocked, skipping server auth tests", allow_module_level=True)

client = TestClient(app)

def test_websocket_connect_no_token_fails():
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws/command") as websocket:
            pass
    assert excinfo.value.code == 1008

def test_websocket_connect_invalid_token_fails():
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws/command", headers={"X-GOD-MODE-TOKEN": "wrong-token"}) as websocket:
            pass
    assert excinfo.value.code == 1008

def test_websocket_connect_valid_token_succeeds():
    # We need to patch where config is used in server.py
    # server.py imports config.
    # Since config is imported as a module 'import config', we patch 'config.GOD_MODE_TOKEN'.
    with patch("config.GOD_MODE_TOKEN", "test-token"):
        with client.websocket_connect("/ws/command", headers={"X-GOD-MODE-TOKEN": "test-token"}) as websocket:
            # Should not raise
            # Send a dummy message to verify connection is open
             pass
