import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock
from modules.system.telemetry import TelemetryCollector
from modules.system.server import SimulationServer
from modules.system.server_bridge import TelemetryExchange, CommandQueue
from pydantic import BaseModel

class TestTelemetryPurity:
    def test_telemetry_collector_returns_pydantic_model(self):
        """
        Verify that TelemetryCollector.harvest() returns a Pydantic BaseModel.
        This enforces DTO purity.
        """
        # Setup
        registry = MagicMock()
        registry.get.return_value = "some_value"

        collector = TelemetryCollector(registry)
        collector.subscribe(["some.path"])

        # Action
        snapshot = collector.harvest(current_tick=1)

        # Assertion
        # This will fail until we refactor TelemetrySnapshotDTO to be a Pydantic model
        assert isinstance(snapshot, BaseModel), f"Expected Pydantic BaseModel, got {type(snapshot)}"

        # Verify content
        if isinstance(snapshot, BaseModel):
            data = snapshot.model_dump()
            assert data["tick"] == 1
            assert data["data"]["some.path"] == "some_value"

    @pytest.mark.asyncio
    async def test_simulation_server_serializes_pydantic_model(self):
        """
        Verify that SimulationServer correctly handles Pydantic models
        during JSON serialization for WebSockets.
        """
        # Setup
        command_queue = CommandQueue()
        telemetry_exchange = TelemetryExchange()

        server = SimulationServer("localhost", 0, command_queue, telemetry_exchange)

        # Create a dummy Pydantic model representing the future TelemetrySnapshotDTO
        class DummySnapshot(BaseModel):
            tick: int
            data: str
            timestamp: float = 0.0

        snapshot = DummySnapshot(tick=10, data="test_data")

        # Mock WebSocket
        mock_ws = AsyncMock()
        # Simulate connected client with stale state
        server.client_states[mock_ws] = -1

        # Action
        # This will fail (serialize to string or crash) until we update _send_snapshot
        await server._send_snapshot(mock_ws, snapshot)

        # Assertion
        # Verify send was called with valid JSON string, not a string representation of the object
        mock_ws.send.assert_called_once()
        call_args = mock_ws.send.call_args[0][0]

        try:
            sent_data = json.loads(call_args)
        except json.JSONDecodeError:
            pytest.fail(f"Failed to decode JSON from websocket payload: {call_args}")

        assert sent_data["tick"] == 10
        assert sent_data["data"] == "test_data"
