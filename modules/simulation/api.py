from __future__ import annotations
from typing import Protocol, TypedDict, Any, List, Dict

# --- DTOs ---

class ShockConfigDTO(TypedDict):
    """Configuration for the economic shock."""
    shock_start_tick: int
    shock_end_tick: int
    tfp_multiplier: float  # The factor to multiply the baseline TFP by (e.g., 0.5 for a 50% drop)
    baseline_tfp: float   # The normal TFP value to restore to

class MarketSnapshotDTO(TypedDict):
    """
    Snapshot of key market indicators for analysis modules.
    """
    gdp: float
    cpi: float

# --- Protocols ---

class IAgent(Protocol):
    id: int
    is_active: bool

class IFirm(IAgent, Protocol):
    productivity_factor: float

class IHousehold(IAgent, Protocol):
    inventory: Dict[str, float]

class ICentralBank(Protocol):
    base_rate: float

class IGovernment(Protocol):
    expenditure_this_tick: float
    revenue_this_tick: float
    total_debt: float

class IConfig(Protocol):
    STARVATION_THRESHOLD: float

class ISimulationState(Protocol):
    """
    Protocol defining the subset of simulation state required by observers and injectors.
    Decouples analysis modules from the concrete Simulation engine.
    """
    firms: List[IFirm]
    households: List[IHousehold]
    central_bank: ICentralBank
    government: IGovernment
    config_module: IConfig

    def get_market_snapshot(self) -> MarketSnapshotDTO:
        """
        Retrieves the current market snapshot containing economic indicators like GDP.
        """
        ...

class IShockInjector(Protocol):
    """
    An interface for a component that can inject economic shocks into the simulation.
    It directly manipulates simulation parameters at runtime based on its configuration.
    """
    def __init__(self, config: ShockConfigDTO, simulation: ISimulationState) -> None:
        ...

    def apply(self, current_tick: int) -> None:
        """
        Applies the shock if the simulation is within the shock window.
        This method is expected to be called every tick.
        """
        ...
