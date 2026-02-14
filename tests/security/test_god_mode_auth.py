import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from fastapi import WebSocketDisconnect
from server import app

client = TestClient(app)

def test_websocket_connect_no_token_fails():
    """Verify that connection without X-GOD-MODE-TOKEN is rejected."""
    with patch("config.GOD_MODE_TOKEN", "test-token"):
        with pytest.raises(WebSocketDisconnect) as excinfo:
            with client.websocket_connect("/ws/command") as websocket:
                pass
        # 1008 is Policy Violation
        assert excinfo.value.code == 1008

def test_websocket_connect_invalid_token_fails():
    """Verify that connection with invalid X-GOD-MODE-TOKEN is rejected."""
    with patch("config.GOD_MODE_TOKEN", "test-token"):
        with pytest.raises(WebSocketDisconnect) as excinfo:
            with client.websocket_connect("/ws/command", headers={"X-GOD-MODE-TOKEN": "wrong-token"}) as websocket:
                pass
        assert excinfo.value.code == 1008

def test_websocket_connect_valid_token_succeeds():
    """Verify that connection with valid X-GOD-MODE-TOKEN is accepted."""
    with patch("config.GOD_MODE_TOKEN", "test-token"):
        with client.websocket_connect("/ws/command", headers={"X-GOD-MODE-TOKEN": "test-token"}) as websocket:
            # Should not raise exception
            # Send a dummy message to verify connection is open
            websocket.send_json({"type": "PAUSE", "payload": {}})
            # We don't necessarily expect a response, just that it doesn't close immediately
