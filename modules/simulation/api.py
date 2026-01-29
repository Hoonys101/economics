from __future__ import annotations
from typing import Protocol, TypedDict, Any

# --- DTOs ---

class ShockConfigDTO(TypedDict):
    """Configuration for the economic shock."""
    shock_start_tick: int
    shock_end_tick: int
    tfp_multiplier: float  # The factor to multiply the baseline TFP by (e.g., 0.5 for a 50% drop)
    baseline_tfp: float   # The normal TFP value to restore to

# --- Interfaces ---

class IShockInjector(Protocol):
    """
    An interface for a component that can inject economic shocks into the simulation.
    It directly manipulates simulation parameters at runtime based on its configuration.
    """
    def __init__(self, config: ShockConfigDTO, simulation: Any) -> None:
        ...

    def apply(self, current_tick: int) -> None:
        """
        Applies the shock if the simulation is within the shock window.
        This method is expected to be called every tick.
        """
        ...
