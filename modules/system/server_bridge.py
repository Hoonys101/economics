import queue
from typing import Any, Optional, List, Callable
import threading

# Bridge Types
CommandQueue = queue.Queue

class TelemetryExchange:
    """
    Thread-safe container for the latest telemetry snapshot.
    Supports observer pattern for event-driven updates.
    """
    def __init__(self):
        self._data: Any = None
        self._lock = threading.Lock()
        self._listeners: List[Callable[[], None]] = []

    def update(self, data: Any) -> None:
        """Atomically updates the snapshot and notifies listeners."""
        with self._lock:
            self._data = data

        # Notify listeners outside the lock to prevent deadlocks
        # Make a copy of listeners to be safe during iteration
        with self._lock:
            current_listeners = list(self._listeners)

        for listener in current_listeners:
            try:
                listener()
            except Exception:
                # Suppress listener errors to avoid breaking the update loop
                pass

    def get(self) -> Optional[Any]:
        """Atomically retrieves the latest snapshot."""
        with self._lock:
            return self._data

    def subscribe(self, callback: Callable[[], None]) -> None:
        """Registers a callback to be invoked on updates."""
        with self._lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def unsubscribe(self, callback: Callable[[], None]) -> None:
        """Unregisters a callback."""
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)
