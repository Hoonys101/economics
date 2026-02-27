from _typeshed import Incomplete
from simulation.agents.government import Government as Government
from simulation.core_agents import Household as Household
from simulation.dtos.api import SimulationState as SimulationState
from simulation.models import Order as Order, Transaction as Transaction
from simulation.portfolio import Portfolio as Portfolio
from typing import Any

logger: Incomplete

class InheritanceManager:
    """
    Phase 22 (WO-049): Legacy Protocol
    Handles Death, Valuation, Taxation (Liquidation), and Transfer.
    Ensures 'Zero Leak' and atomic settlement via SettlementSystem.
    """
    config_module: Incomplete
    logger: Incomplete
    def __init__(self, config_module: Any) -> None: ...
    def process_death(self, deceased: Household, government: Government, simulation: SimulationState) -> list[Transaction]:
        """
        Executes the inheritance pipeline using SettlementSystem (Atomic).

        Args:
            deceased: The agent who died.
            government: The entity collecting tax.
            simulation: Access to markets/registry for valuation and settlement_system.

        Returns:
            List[Transaction]: Ordered list of executed transaction receipts.
        """
