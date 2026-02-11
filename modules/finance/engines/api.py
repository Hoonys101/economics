from typing import TypedDict, Protocol, runtime_checkable, Optional

class MonetaryStateDTO(TypedDict):
    """Input state from CentralBank agent."""
    tick: int
    current_base_rate: float
    potential_gdp: float # Calculated and owned by the agent
    inflation_target: float
    # Optional Strategy Overrides (WO-136)
    override_target_rate: Optional[float]
    rate_multiplier: Optional[float]

class MarketSnapshotDTO(TypedDict):
    """Shared market data for both engines."""
    tick: int
    inflation_rate_annual: float
    current_gdp: float

class MonetaryDecisionDTO(TypedDict):
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
