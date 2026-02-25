from modules.system.api import MarketSignalDTO as MarketSignalDTO, MarketSnapshotDTO as MarketSnapshotDTO
from simulation.dtos.api import DecisionInputDTO as DecisionInputDTO, SimulationState as SimulationState
from simulation.world_state import WorldState as WorldState
from typing import Any, Protocol

class IPhaseStrategy(Protocol):
    """Interface for a single phase of the simulation tick."""
    def execute(self, state: SimulationState) -> SimulationState:
        """
        Executes the logic for this phase.

        Args:
            state: The current simulation state DTO for the tick.

        Returns:
            The potentially modified simulation state DTO.
        """

class IMarketSignalFactory(Protocol):
    """Defines the contract for creating market signals from the current market state."""
    def create_market_signals(self, markets: dict[str, Any]) -> dict[str, MarketSignalDTO]:
        """
        Iterates through markets and generates a comprehensive dictionary of MarketSignalDTOs.

        Args:
            markets: The dictionary of all market objects from the SimulationState.

        Returns:
            A dictionary mapping item_id to its corresponding MarketSignalDTO.
        """

class IDecisionInputFactory(Protocol):
    """Defines the contract for assembling the main DecisionInputDTO for agents."""
    def create_decision_input(self, state: SimulationState, world_state: WorldState, market_snapshot: MarketSnapshotDTO) -> DecisionInputDTO:
        """
        Constructs the primary input DTO used for all agent decisions in the phase.
        This encapsulates the creation of various financial and governmental contexts.

        Args:
            state: The current SimulationState DTO.
            world_state: The simulation's WorldState object, required for accessing systems
                         and state not present in the SimulationState DTO (e.g., trackers).
            market_snapshot: The snapshot of market signals for the current tick.

        Returns:
            A fully populated DecisionInputDTO.
        """
