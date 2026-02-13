import asyncio
import threading
import json
import logging
import websockets
from dataclasses import asdict, is_dataclass
from typing import Optional, List
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
        self._stop_event = asyncio.Event()

    def start(self):
        """Starts the server in a separate thread."""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info(f"SimulationServer thread started on {self.host}:{self.port}")

    def _run(self):
        asyncio.run(self._serve())

    async def _serve(self):
        try:
            async with websockets.serve(self._handler, self.host, self.port):
                logger.info("WebSocket server running...")
                # Keep running until stop event or indefinitely
                await asyncio.Future() # run forever
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")

    async def _handler(self, websocket):
        self.connected_clients.add(websocket)
        logger.info(f"Client connected: {websocket.remote_address}")

        # Start broadcast task for this client
        broadcast_task = asyncio.create_task(self._broadcast_loop(websocket))

        try:
            async for message in websocket:
                await self._process_message(message)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
        finally:
            self.connected_clients.remove(websocket)
            broadcast_task.cancel()
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

    async def _broadcast_loop(self, websocket):
        last_tick = -1
        while True:
            snapshot = self.telemetry_exchange.get()
            if snapshot and getattr(snapshot, 'tick', -1) > last_tick:
                try:
                    # Serialize
                    payload = asdict(snapshot) if is_dataclass(snapshot) else snapshot
                    await websocket.send(json.dumps(payload, default=str))
                    last_tick = snapshot.tick
                except Exception as e:
                    logger.error(f"Broadcast failed: {e}")
                    break
            await asyncio.sleep(0.1) # 10Hz poll
