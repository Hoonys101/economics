import pytest
import asyncio
import websockets
import threading
import time
import socket
from unittest.mock import MagicMock
from modules.system.server import SimulationServer

if isinstance(websockets, MagicMock):
    pytest.skip("websockets is mocked, skipping server auth tests", allow_module_level=True)
from modules.system.server_bridge import CommandQueue, TelemetryExchange
from modules.simulation.dtos.api import ServerConfigDTO

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

    config = ServerConfigDTO(host="127.0.0.1", port=server_port, god_mode_token=token)
    srv = SimulationServer(config, cq, te)
    srv.start()

    # Wait for server to start accepting connections using polling
    start_time = time.time()
    # Wait for server thread to actually bind and listen
    # We can try connecting to verify it's up
    while time.time() - start_time < 5.0:
        try:
            # Try to connect with a dummy socket to check if port is open
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', server_port))
            sock.close()
            if result == 0:
                break
        except Exception:
            pass
        time.sleep(0.1)
    else:
        pytest.fail("Server failed to start within timeout")

    # Yield server and token
    yield srv, token

    # Ideally stop server here but SimulationServer doesn't have a clean stop yet in tests

# --- Tests ---

@pytest.mark.asyncio
async def test_auth_success(server_instance):
    server, token = server_instance
    # server.host is now a property returning config.host
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
        async with websockets.connect(uri, additional_headers=headers):
            pass
    # InvalidStatus stores the response object
    assert excinfo.value.response.status_code == 401

@pytest.mark.asyncio
async def test_auth_failure_missing_token(server_instance):
    server, token = server_instance
    uri = f"ws://{server.host}:{server.port}"

    # No headers
    with pytest.raises(websockets.exceptions.InvalidStatus) as excinfo:
        async with websockets.connect(uri):
            pass
    assert excinfo.value.response.status_code == 401
