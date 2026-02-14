import pytest
import asyncio
import websockets
import threading
import time
import socket
from modules.system.server import SimulationServer
from modules.system.server_bridge import CommandQueue, TelemetryExchange

# --- Fixtures ---

@pytest.fixture(scope="function")
def server_port():
    """Get a free port."""
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

@pytest.fixture(scope="function")
def server_instance(server_port):
    """Start a SimulationServer instance in a separate thread."""
    cq = CommandQueue()
    te = TelemetryExchange()
    token = "secret-token-123"

    srv = SimulationServer("localhost", server_port, cq, te, god_mode_token=token)
    srv.start()

    # Wait for server to start accepting connections
    # Simple retry logic or sleep
    time.sleep(1)

    yield srv, token

# --- Tests ---

@pytest.mark.asyncio
async def test_auth_success(server_instance):
    server, token = server_instance
    uri = f"ws://{server.host}:{server.port}"

    headers = {"X-GOD-MODE-TOKEN": token}
    try:
        async with websockets.connect(uri, additional_headers=headers) as ws:
            # If we get here, handshake was successful (HTTP 101)
            # Send a ping to verify connection is truly alive
            await ws.ping()
    except Exception as e:
        pytest.fail(f"Connection failed with valid token: {e}")

@pytest.mark.asyncio
async def test_auth_failure_invalid_token(server_instance):
    server, token = server_instance
    uri = f"ws://{server.host}:{server.port}"

    headers = {"X-GOD-MODE-TOKEN": "wrong-token"}
    # Use InvalidStatus for newer websockets versions
    with pytest.raises(websockets.exceptions.InvalidStatus) as excinfo:
        async with websockets.connect(uri, additional_headers=headers) as ws:
            pass
    # InvalidStatus stores the response object, check status_code on it (or just the exception itself has it depending on version)
    # response attribute has status_code
    assert excinfo.value.response.status_code == 401

@pytest.mark.asyncio
async def test_auth_failure_missing_token(server_instance):
    server, token = server_instance
    uri = f"ws://{server.host}:{server.port}"

    # No headers
    with pytest.raises(websockets.exceptions.InvalidStatus) as excinfo:
        async with websockets.connect(uri) as ws:
            pass
    assert excinfo.value.response.status_code == 401
