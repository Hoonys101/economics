from _typeshed import Incomplete
from simulation.core_agents import Household as Household
from simulation.firms import Firm as Firm
from simulation.models import Transaction as Transaction
from simulation.world_state import WorldState as WorldState
from typing import Any, Callable

logger: Incomplete

class ActionProcessor:
    """
    Processes actions and transactions in the simulation.
    Decomposed from Simulation engine.
    WO-103: Adapts legacy calls to SystemInterface.
    """
    world_state: Incomplete
    def __init__(self, world_state: WorldState) -> None: ...
    def process_transactions(self, transactions: list[Transaction], market_data_callback: Callable[[], Any]) -> None:
        """
        Delegates transaction processing to the TransactionProcessor system using SimulationState.

        WARNING: This method executes transactions immediately. It should ONLY be used for
        legacy tests or isolated execution. Do NOT use this within the TickOrchestrator loop
        as it will cause double-execution when combined with the drain mechanism.
        """
    def process_stock_transactions(self, transactions: list[Transaction]) -> None:
        """Process stock transactions."""
