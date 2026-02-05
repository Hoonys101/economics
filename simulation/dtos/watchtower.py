from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class TheWatchtowerSnapshotDTO:
    """The root DTO for The Watchtower dashboard, sent via WebSocket every N ticks."""
    tick: int
    status: str = "RUNNING" # RUNNING, PAUSED, EMERGENCY
    integrity: Dict[str, float] = field(default_factory=lambda: {"m2_leak": 0.0, "fps": 0.0})
    macro: Dict[str, float] = field(default_factory=lambda: {"gdp": 0.0, "cpi": 0.0, "unemploy": 0.0, "gini": 0.0})
    finance: Dict[str, Any] = field(default_factory=lambda: {
        "rates": {"base": 0.0, "call": 0.0, "loan": 0.0, "savings": 0.0},
        "supply": {"m0": 0.0, "m1": 0.0, "m2": 0.0, "velocity": 0.0}
    })
    politics: Dict[str, Any] = field(default_factory=lambda: {
        "approval": {"total": 0.0, "low": 0.0, "mid": 0.0, "high": 0.0},
        "status": {"ruling_party": "NEUTRAL", "cohesion": 0.5},
        "fiscal": {"revenue": 0.0, "welfare": 0.0, "debt": 0.0}
    })
    population: Dict[str, Any] = field(default_factory=lambda: {
        "distribution": {"q1": 0.0, "q2": 0.0, "q3": 0.0, "q4": 0.0, "q5": 0.0},
        "active_count": 0,
        "metrics": {"birth": 0.0, "death": 0.0}
    })
