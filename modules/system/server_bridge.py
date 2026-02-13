import queue
from typing import Any, Optional
import threading

# Bridge Types
CommandQueue = queue.Queue

class TelemetryExchange:
    """
    Thread-safe container for the latest telemetry snapshot.
    """
    def __init__(self):
        self._data: Any = None
        self._lock = threading.Lock()

    def update(self, data: Any) -> None:
        """Atomically updates the snapshot."""
        with self._lock:
            self._data = data

    def get(self) -> Optional[Any]:
        """Atomically retrieves the latest snapshot."""
        with self._lock:
            return self._data
