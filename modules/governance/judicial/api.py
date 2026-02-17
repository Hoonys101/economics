from typing import TypedDict, List, Optional, Protocol, Dict
from dataclasses import dataclass

# Common/System Imports
from modules.system.api import AgentID, CurrencyCode

# DTOs
@dataclass
class JudicialConfigDTO:
    """Configuration for the Judicial System."""
    seizure_threshold: int = 0
    legal_fee_percent: float = 0.0
    bankruptcy_threshold: int = -1000  # Debt level triggering bankruptcy

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
    liquidated_assets: Dict[str, int]  # Details of what was sold

class IJudicialSystem(Protocol):
    """
    Interface for the Judicial System.
    Orchestrates debt recovery and bankruptcy proceedings.
    """

    def handle_default(self, event: 'LoanDefaultedEvent') -> SeizureResultDTO:
        """
        Process a loan default event using the Waterfall Recovery Logic.
        1. Cash Seizure
        2. Stock Seizure (Liquidation/Transfer)
        3. Inventory Seizure (Liquidation)
        """
        ...

    def assess_solvency(self, agent_id: AgentID) -> bool:
        """
        Check if an agent is solvent based on SSoT balances and assets.
        """
        ...

# Events
class LoanDefaultedEvent(TypedDict):
    event_type: str  # "LOAN_DEFAULTED"
    tick: int
    agent_id: AgentID
    loan_id: str
    defaulted_amount: int  # Pennies
    creditor_id: AgentID

class DebtRestructuringRequiredEvent(TypedDict):
    event_type: str # "DEBT_RESTRUCTURING_REQUIRED"
    tick: int
    debtor_id: AgentID
    creditor_id: AgentID
    remaining_debt: int
    loan_id: str
