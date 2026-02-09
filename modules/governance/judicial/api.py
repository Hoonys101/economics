from typing import Protocol, TYPE_CHECKING
from dataclasses import dataclass
from modules.events.dtos import FinancialEvent

if TYPE_CHECKING:
    from simulation.finance.api import ISettlementSystem
    from modules.system.api import IAgentRegistry
    from modules.finance.api import IShareholderRegistry

@dataclass
class SeizureWaterfallResultDTO:
    """Result of the judicial asset seizure process."""
    success: bool
    total_seized: float
    remaining_debt: float
    cash_seized: float
    stocks_seized_value: float
    inventory_seized_value: float

class IJudicialSystem(Protocol):
    """
    Handles the consequences of events based on simulation rules.
    It subscribes to the EventBus and acts upon financial events
    to enforce governance and legal statutes.
    """

    def handle_financial_event(self, event: FinancialEvent) -> None:
        """
        Primary entry point for processing events from the EventBus.
        This method delegates to specific handlers based on the event's type.
        """
        ...

    def apply_default_penalty(self, agent_id: int, defaulted_amount: float, loan_id: str, tick: int) -> None:
        """
        Applies non-financial penalties for a loan default, such as
        reducing reputation or experience points, and freezing credit.
        """
        ...

    def execute_seizure_waterfall(self, agent_id: int, creditor_id: int, amount: float, loan_id: str, tick: int) -> SeizureWaterfallResultDTO:
        """
        Executes a hierarchical asset seizure (Cash -> Stocks -> Inventory)
        to recover the defaulted amount.
        """
        ...
