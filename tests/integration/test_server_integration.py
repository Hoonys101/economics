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
from simulation.dtos.config_dtos import ServerConfigDTO

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

    config = ServerConfigDTO(host="127.0.0.1", port=port, god_mode_token="test-token")
    srv = SimulationServer(config, cq, te)
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

    # Wait for server to be fully ready
    await asyncio.sleep(0.5)

    async with websockets.connect(uri, additional_headers={"X-GOD-MODE-TOKEN": "test-token"}) as ws:
        await ws.send(json.dumps(payload))
        # Give server time to process
        await asyncio.sleep(0.5)

    assert not cq.empty()
    cmd = cq.get()
    assert str(cmd.command_id) == cmd_id
    assert cmd.parameter_key == "tax_rate"
    assert cmd.new_value == 0.15

@pytest.mark.asyncio
async def test_telemetry_broadcast(server, bridge):
    from simulation.dtos.telemetry import TelemetrySnapshotDTO

    # Wait for server to be fully ready
    await asyncio.sleep(0.5)

    cq, te = bridge
    uri = f"ws://{server.host}:{server.port}"

    # We need to construct a valid TelemetrySnapshotDTO
    # Since existing tests pass, we assume import works.
    # But wait, snapshot_10 uses named args, but TelemetrySnapshotDTO is a Pydantic model now?
    # Or dataclass?
    # Let's check TelemetrySnapshotDTO definition if needed.
    # Assuming the test code was valid before, I just update server init.

    # Wait, I am overwriting the file. I should preserve imports and logic.
    # The read output had:
    # from simulation.dtos.telemetry import TelemetrySnapshotDTO
    # inside the function.

    # Just reusing the logic from the read file with server init fix.

    # Re-reading to ensure I don't miss anything.
    # The previous file content has valid imports.

    snapshot_10 = TelemetrySnapshotDTO(
        timestamp=100.0,
        tick=10,
        data={"message": "test"},
        errors=[],
        metadata={}
    )

    te.update(snapshot_10)

    async with websockets.connect(uri, additional_headers={"X-GOD-MODE-TOKEN": "test-token"}) as ws:
        # Wait for broadcast (Server sends latest on connect or loop)
        # Our loop waits for update. But if update happened before connect?
        # Server loop: while True: snapshot = get(); if snapshot.tick > last_tick: send().
        # last_tick starts at -1.
        # So if we update before connect, the server loop (running for that client) will pick it up immediately.

        msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
        data = json.loads(msg)
        assert data["tick"] == 10
        assert data["data"]["message"] == "test"

        # Test Duplicate Tick Suppression
        # Create a new object with same tick (different content to verify it's NOT sent)
        snapshot_10_dup = TelemetrySnapshotDTO(
            timestamp=100.1,
            tick=10,
            data={"message": "test_dup"},
            errors=[],
            metadata={}
        )
        te.update(snapshot_10_dup)
        try:
             await asyncio.wait_for(ws.recv(), timeout=0.5)
             # If we receive something, it's a failure (duplicate sent)
             # But wait, we might receive the previous one again if we reconnected? No, we are in same session.
             # The server checks last_sent_tick.
             # If last_sent_tick is 10, and new snapshot is 10, it won't send.
             # So timeout is expected.
             # If we receive, assert False.
             received = json.loads(await ws.recv()) # consume if any
             assert False, f"Should not receive duplicate tick: {received}"
        except asyncio.TimeoutError:
             pass

        # Test New Tick
        snapshot_11 = TelemetrySnapshotDTO(
            timestamp=101.0,
            tick=11,
            data={"message": "update"},
            errors=[],
            metadata={}
        )
        te.update(snapshot_11)

        msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
        data = json.loads(msg)
        assert data["tick"] == 11
        assert data["data"]["message"] == "update"
