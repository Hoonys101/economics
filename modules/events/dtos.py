from typing import TypedDict, Literal, Union

class LoanDefaultedEvent(TypedDict):
    """
    Event emitted when a borrower defaults on a loan.
    Used by the JudicialSystem to apply non-financial consequences.
    """
    event_type: Literal["LOAN_DEFAULTED"]
    tick: int
    agent_id: int
    loan_id: str
    defaulted_amount: float
    creditor_id: int

class InsolvencyDeclaredEvent(TypedDict):
    """
    Event emitted when an agent is declared insolvent (liabilities > assets).
    """
    event_type: Literal["INSOLVENCY_DECLARED"]
    tick: int
    agent_id: int
    total_debt: float
    total_assets: float

class DebtRestructuringRequiredEvent(TypedDict):
    """
    Event emitted when a borrower still has outstanding debt after
    the judicial seizure waterfall (Cash -> Stocks -> Inventory) has been exhausted.
    """
    event_type: Literal["DEBT_RESTRUCTURING_REQUIRED"]
    tick: int
    agent_id: int
    remaining_debt: float
    creditor_id: int

# A union type for all financial events
FinancialEvent = Union[LoanDefaultedEvent, InsolvencyDeclaredEvent, DebtRestructuringRequiredEvent]
