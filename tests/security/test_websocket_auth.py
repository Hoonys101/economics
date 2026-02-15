import pytest
import asyncio
import websockets
import time
import socket
from modules.system.server import SimulationServer
from modules.system.server_bridge import CommandQueue, TelemetryExchange
from simulation.dtos.config_dtos import ServerConfigDTO

@pytest.fixture
def bridge():
    cq = CommandQueue()
    te = TelemetryExchange()
    return cq, te

@pytest.fixture
def server(bridge):
    cq, te = bridge
    # Use a random port to avoid conflicts
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()

    config = ServerConfigDTO(host="127.0.0.1", port=port, god_mode_token="secret-token-123")
    srv = SimulationServer(config, cq, te)
    srv.start()
    # Wait for server startup
    time.sleep(1)
    return srv

@pytest.mark.asyncio
async def test_auth_success(server):
    """Verifies that connection is accepted with valid token."""
    uri = f"ws://{server.host}:{server.port}"
    async with websockets.connect(uri, additional_headers={"X-GOD-MODE-TOKEN": "secret-token-123"}) as ws:
        # Connection should be established
        # Send a ping to verify connection is alive
        pong = await ws.ping()
        await pong
        # If we reached here, connection is good

@pytest.mark.asyncio
async def test_auth_missing_token(server):
    """Verifies that connection is rejected (401) when token is missing."""
    uri = f"ws://{server.host}:{server.port}"
    with pytest.raises(websockets.exceptions.InvalidStatus) as exc:
        async with websockets.connect(uri):
            pass
    assert exc.value.response.status_code == 401

@pytest.mark.asyncio
async def test_auth_invalid_token(server):
    """Verifies that connection is rejected (401) when token is invalid."""
    uri = f"ws://{server.host}:{server.port}"
    with pytest.raises(websockets.exceptions.InvalidStatus) as exc:
        async with websockets.connect(uri, additional_headers={"X-GOD-MODE-TOKEN": "wrong-token"}):
            pass
    assert exc.value.response.status_code == 401
