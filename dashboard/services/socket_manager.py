import threading
import asyncio
import json
import time
from typing import Optional, List, Dict, Any
from queue import Queue, Empty
import websockets
from dataclasses import asdict

from simulation.dtos.commands import GodCommandDTO

class SocketManager:
    """
    Singleton service to manage WebSocket connection in a background thread.
    Handles command sending and telemetry/audit reception.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SocketManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._uri = "ws://localhost:8765"
        self._stop_event = threading.Event()
        self._connection_status = "Disconnected"

        self.command_queue = Queue()
        self.telemetry_queue = Queue()
        self.audit_log_queue = Queue()

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    @property
    def connection_status(self):
        return self._connection_status

    def _run_loop(self):
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._async_loop())
        loop.close()

    async def _async_loop(self):
        while not self._stop_event.is_set():
            try:
                self._connection_status = "Connecting..."
                async with websockets.connect(self._uri) as websocket:
                    self._connection_status = "Connected"

                    while not self._stop_event.is_set():
                        # Send pending commands
                        try:
                            while not self.command_queue.empty():
                                cmd = self.command_queue.get_nowait()
                                payload = json.dumps(asdict(cmd), default=str)
                                await websocket.send(payload)
                        except Empty:
                            pass
                        except Exception as e:
                            print(f"Send error: {e}")

                        # Receive messages
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                            data = json.loads(message)

                            if "tick" in data and "integrity" in data:
                                self.telemetry_queue.put(data)
                            elif "command_id" in data:
                                self.audit_log_queue.put(data)
                        except asyncio.TimeoutError:
                            pass
                        except Exception as e:
                            # Log error but don't crash loop
                            pass

                        await asyncio.sleep(0.01)

            except Exception:
                self._connection_status = "Disconnected"
                await asyncio.sleep(1) # Retry delay

    def send_command(self, command: GodCommandDTO):
        self.command_queue.put(command)

    def get_latest_telemetry(self) -> Optional[Dict[str, Any]]:
        """
        Returns the most recent telemetry data, clearing older buffered items.
        """
        item = None
        while not self.telemetry_queue.empty():
            item = self.telemetry_queue.get_nowait()
        return item

    def get_audit_logs(self) -> List[Dict[str, Any]]:
        """
        Returns all accumulated audit logs.
        """
        logs = []
        while not self.audit_log_queue.empty():
            logs.append(self.audit_log_queue.get_nowait())
        return logs
