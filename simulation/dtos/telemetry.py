from typing import Dict, List, Any
from pydantic import BaseModel

class TelemetrySnapshotDTO(BaseModel):
    """
    Real-time data snapshot structure for telemetry broadcasting.
    Represents a snapshot of telemetry data collected at a specific tick.

    Fields:
        timestamp: Unix timestamp of when the snapshot was taken.
        tick: The simulation tick this snapshot corresponds to.
        data: A dictionary of collected data fields, where keys are dot-notation paths (e.g., 'firm.101.profit').
        errors: A list of field paths that failed to be collected.
        metadata: Additional metadata such as sampling frequency or collector stats.
    """
    timestamp: float      # Unix Timestamp
    tick: int            # Simulation Tick
    data: Dict[str, Any] # Collected Data Fields (Dot-notation key)
    errors: List[str]    # List of failed field paths
    metadata: Dict[str, Any] # Metadata (e.g., sampling stats)
