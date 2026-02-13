import pytest
import threading
import time
import json
import asyncio
import websockets
from uuid import uuid4
from dataclasses import dataclass
from modules.system.server_bridge import CommandQueue, TelemetryExchange
from modules.system.server import SimulationServer
from unittest.mock import MagicMock

# --- Fixtures ---

@pytest.fixture
def bridge():
    cq = CommandQueue()
    te = TelemetryExchange()
    return cq, te

@pytest.fixture
def server(bridge):
    cq, te = bridge
    # Use a random port to avoid conflicts
    import socket
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()

    srv = SimulationServer("localhost", port, cq, te)
    srv.start()
    # Wait for server startup
    time.sleep(1)
    return srv

# --- Tests ---

@pytest.mark.asyncio
async def test_command_injection(server, bridge):
    cq, te = bridge
    uri = f"ws://{server.host}:{server.port}"

    cmd_id = str(uuid4())
    payload = {
        "command_id": cmd_id,
        "target_domain": "Economy",
        "parameter_key": "tax_rate",
        "new_value": 0.15,
        "command_type": "SET_PARAM"
    }

    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps(payload))
        # Give server time to process
        await asyncio.sleep(0.2)

    assert not cq.empty()
    cmd = cq.get()
    assert str(cmd.command_id) == cmd_id
    assert cmd.parameter_key == "tax_rate"

@pytest.mark.asyncio
async def test_telemetry_broadcast(server, bridge):
    cq, te = bridge
    uri = f"ws://{server.host}:{server.port}"

    @dataclass
    class SimpleDTO:
        tick: int
        data: str

    te.update(SimpleDTO(tick=10, data="test"))

    async with websockets.connect(uri) as ws:
        # Wait for broadcast (Server sends latest on connect or loop)
        # Our loop waits for update. But if update happened before connect?
        # Server loop: while True: snapshot = get(); if snapshot.tick > last_tick: send().
        # last_tick starts at -1.
        # So if we update before connect, the server loop (running for that client) will pick it up immediately.

        msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
        data = json.loads(msg)
        assert data["tick"] == 10
        assert data["data"] == "test"

        # Test Duplicate Tick Suppression
        te.update(SimpleDTO(tick=10, data="test_dup"))
        try:
             await asyncio.wait_for(ws.recv(), timeout=0.5)
             assert False, "Should not receive duplicate tick"
        except asyncio.TimeoutError:
             pass

        # Test New Tick
        te.update(SimpleDTO(tick=11, data="update"))

        msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
        data = json.loads(msg)
        assert data["tick"] == 11
        assert data["data"] == "update"
