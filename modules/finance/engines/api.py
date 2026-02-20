from typing import List, Optional, Protocol, runtime_checkable
from dataclasses import dataclass
from modules.system.api import MarketSnapshotDTO

@dataclass(frozen=True)
class MonetaryStateDTO:
    """Input state from CentralBank agent."""
    tick: int
    current_base_rate: float
    potential_gdp: float # Calculated and owned by the agent
    inflation_target: float
    # Optional Strategy Overrides (WO-136)
    override_target_rate: Optional[float] = None
    rate_multiplier: Optional[float] = None

@dataclass(frozen=True)
class MonetaryDecisionDTO:
    """Output decision from the MonetaryEngine."""
    new_base_rate: float

@runtime_checkable
class IMonetaryEngine(Protocol):
    def calculate_rate(
        self,
        state: MonetaryStateDTO,
        market: MarketSnapshotDTO
    ) -> MonetaryDecisionDTO:
        """
        Calculates the new target base interest rate.
        """
        ...
