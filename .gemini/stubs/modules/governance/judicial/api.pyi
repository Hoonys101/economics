from dataclasses import dataclass
from modules.system.api import AgentID as AgentID, CurrencyCode as CurrencyCode
from typing import Protocol, TypedDict

@dataclass
class JudicialConfigDTO:
    """Configuration for the Judicial System."""
    seizure_threshold: int = ...
    legal_fee_percent: float = ...
    bankruptcy_threshold: int = ...

@dataclass
class SeizureRequestDTO:
    """DTO for requesting asset seizure."""
    debtor_id: AgentID
    creditor_id: AgentID
    target_amount: int
    currency: CurrencyCode
    loan_id: str

@dataclass
class SeizureResultDTO:
    """Result of a seizure operation."""
    seized_cash: int
    seized_stocks_value: int
    seized_inventory_value: int
    remaining_debt: int
    is_fully_recovered: bool
    liquidated_assets: dict[str, int]

class IJudicialSystem(Protocol):
    """
    Interface for the Judicial System.
    Orchestrates debt recovery and bankruptcy proceedings.
    """
    def handle_default(self, event: LoanDefaultedEvent) -> SeizureResultDTO:
        """
        Process a loan default event using the Waterfall Recovery Logic.
        1. Cash Seizure
        2. Stock Seizure (Liquidation/Transfer)
        3. Inventory Seizure (Liquidation)
        """
    def assess_solvency(self, agent_id: AgentID) -> bool:
        """
        Check if an agent is solvent based on SSoT balances and assets.
        """

class LoanDefaultedEvent(TypedDict):
    event_type: str
    tick: int
    agent_id: AgentID
    loan_id: str
    defaulted_amount: int
    creditor_id: AgentID

class DebtRestructuringRequiredEvent(TypedDict):
    event_type: str
    tick: int
    debtor_id: AgentID
    creditor_id: AgentID
    remaining_debt: int
    loan_id: str
