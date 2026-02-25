import queue
from modules.system.api import MarketSnapshotDTO as MarketSnapshotDTO
from simulation.dtos.telemetry import TelemetrySnapshotDTO
from typing import Callable

CommandQueue = queue.Queue

class TelemetryExchange:
    """
    Thread-safe container for the latest telemetry snapshot.
    Supports observer pattern for event-driven updates.
    """
    def __init__(self) -> None: ...
    def update(self, data: TelemetrySnapshotDTO | MarketSnapshotDTO) -> None:
        """Atomically updates the snapshot and notifies listeners."""
    def get(self) -> TelemetrySnapshotDTO | MarketSnapshotDTO | None:
        """Atomically retrieves the latest snapshot."""
    def subscribe(self, callback: Callable[[], None]) -> None:
        """Registers a callback to be invoked on updates."""
    def unsubscribe(self, callback: Callable[[], None]) -> None:
        """Unregisters a callback."""
