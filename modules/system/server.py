import asyncio
import threading
import json
import logging
import websockets
from dataclasses import asdict, is_dataclass
from typing import Optional, List, Dict
from uuid import UUID
from simulation.dtos.commands import GodCommandDTO
from modules.system.server_bridge import CommandQueue, TelemetryExchange

logger = logging.getLogger("SimulationServer")

class SimulationServer:
    def __init__(self, host: str, port: int, command_queue: CommandQueue, telemetry_exchange: TelemetryExchange):
        self.host = host
        self.port = port
        self.command_queue = command_queue
        self.telemetry_exchange = telemetry_exchange
        self.connected_clients = set()
        self.client_states: Dict[websockets.WebSocketServerProtocol, int] = {}
        self._stop_event = asyncio.Event()

    def start(self):
        """Starts the server in a separate thread."""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info(f"SimulationServer thread started on {self.host}:{self.port}")

    def _run(self):
        asyncio.run(self._serve())

    async def _serve(self):
        loop = asyncio.get_running_loop()

        # Define callback to be triggered by Simulation Engine (Thread A)
        # It schedules the broadcast task on the Server Loop (Thread B)
        def on_tick():
            loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self._broadcast_to_all())
            )

        # Register event listener
        self.telemetry_exchange.subscribe(on_tick)

        try:
            async with websockets.serve(self._handler, self.host, self.port):
                logger.info("WebSocket server running...")
                # Keep running until stop event or indefinitely
                await asyncio.Future() # run forever
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
        finally:
            self.telemetry_exchange.unsubscribe(on_tick)

    async def _handler(self, websocket):
        self.connected_clients.add(websocket)
        logger.info(f"Client connected: {websocket.remote_address}")

        # Initialize per-client state to track sent data
        # Use explicit dictionary to store client state, avoiding attribute injection on websocket object
        self.client_states[websocket] = -1

        # Send initial snapshot immediately if available
        current_snapshot = self.telemetry_exchange.get()
        if current_snapshot:
            await self._send_snapshot(websocket, current_snapshot)

        try:
            async for message in websocket:
                await self._process_message(message)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
        finally:
            self.connected_clients.remove(websocket)
            if websocket in self.client_states:
                del self.client_states[websocket]
            logger.info(f"Client disconnected: {websocket.remote_address}")

    async def _process_message(self, message: str):
        try:
            data = json.loads(message)
            # Deserialize to GodCommandDTO
            # Assuming JSON structure matches DTO fields
            # We might need a helper to convert dict to DTO
            # Basic validation
            if "command_id" in data and isinstance(data["command_id"], str):
                 # Convert string UUID to object if required, or DTO handles it?
                 # GodCommandDTO uses UUID field. We must convert.
                 try:
                     data["command_id"] = UUID(data["command_id"])
                 except:
                     pass # Let DTO validation fail if invalid

            cmd = GodCommandDTO(**data)
            self.command_queue.put(cmd)
            logger.debug(f"Command enqueued: {cmd.command_id}")
        except Exception as e:
            logger.error(f"Invalid command received: {e}")

    async def _broadcast_to_all(self):
        """Fetches the latest snapshot and broadcasts to all clients."""
        snapshot = self.telemetry_exchange.get()
        if not snapshot:
            return

        # Iterate over a copy of connected clients to avoid runtime errors during iteration
        # if a client disconnects concurrently.
        clients = list(self.connected_clients)

        # Use asyncio.gather to broadcast in parallel, or iterate.
        # Iterating is safer for exception handling per client.
        for ws in clients:
            try:
                await self._send_snapshot(ws, snapshot)
            except websockets.exceptions.ConnectionClosed:
                # Disconnection handled in _handler
                pass
            except Exception as e:
                logger.error(f"Failed to send to client: {e}")

    async def _send_snapshot(self, websocket, snapshot):
        """Sends the snapshot to a specific client if it's new."""
        # Check against client's last sent tick
        last_tick = self.client_states.get(websocket, -1)
        current_tick = getattr(snapshot, 'tick', -1)

        if current_tick > last_tick:
            try:
                # Serialize
                payload = asdict(snapshot) if is_dataclass(snapshot) else snapshot
                await websocket.send(json.dumps(payload, default=str))

                # Update client state
                self.client_states[websocket] = current_tick
            except Exception as e:
                # Let caller handle or just re-raise
                raise e
