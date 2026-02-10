from typing import TypedDict, Dict, Optional, List, TypeAlias, Literal
from modules.simulation.api import AgentID

CurrencyCode: TypeAlias = str

class MoneyDTO(TypedDict):
    """Represents a monetary value with its associated currency."""
    amount: float
    currency: CurrencyCode

class MultiCurrencyWalletDTO(TypedDict):
    """Represents a complete portfolio of assets, keyed by currency."""
    balances: Dict[CurrencyCode, float]

class InvestmentOrderDTO(TypedDict):
    """Defines an internal order for investment (e.g., R&D, Capex)."""
    order_type: str # e.g., "INVEST_RD", "INVEST_AUTOMATION"
    investment: MoneyDTO
    target_agent_id: Optional[AgentID] # For M&A, etc.

# --- Bank Decomposition DTOs (TD-274) ---

LoanStatus = Literal["PENDING", "ACTIVE", "PAID", "DEFAULTED"]

class LoanApplicationDTO(TypedDict):
    applicant_id: AgentID
    amount: float
    purpose: str
    term_months: int # Or ticks, depending on usage. Assuming ticks based on Bank code.
    # Spec says term_months, but Bank code uses term_ticks. I'll stick to spec name but note usage.

class LoanDTO(TypedDict):
    loan_id: str
    borrower_id: AgentID
    principal: float
    interest_rate: float
    term_months: int
    remaining_principal: float
    status: LoanStatus
    origination_tick: int
    due_tick: Optional[int]

class DepositDTO(TypedDict):
    owner_id: AgentID
    balance: float
    interest_rate: float
