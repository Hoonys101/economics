from __future__ import annotations
from typing import Dict, Optional, List, TypeAlias, Literal, Any
from dataclasses import dataclass, field
from modules.simulation.api import AgentID

CurrencyCode: TypeAlias = str
LoanStatus = Literal["PENDING", "ACTIVE", "PAID", "DEFAULTED"]

@dataclass
class MoneyDTO:
    """
    Represents a monetary value with its associated currency.
    MIGRATION NOTE: Used to be float 'amount'. Now 'amount_pennies' (int).
    """
    amount_pennies: int
    currency: CurrencyCode

@dataclass
class MultiCurrencyWalletDTO:
    """Represents a complete portfolio of assets, keyed by currency."""
    balances: Dict[CurrencyCode, int] # Pennies

@dataclass
class InvestmentOrderDTO:
    """Defines an internal order for investment (e.g., R&D, Capex)."""
    order_type: str # e.g., "INVEST_RD", "INVEST_AUTOMATION"
    investment: MoneyDTO
    target_agent_id: Optional[AgentID] = None # For M&A, etc.

# --- Bank Decomposition DTOs (TD-274) ---

@dataclass
class LoanApplicationDTO:
    """
    Input for assessing a new loan application.
    Unified DTO merging engine_api and legacy specs.
    """
    borrower_id: AgentID
    amount_pennies: int

    # Optional fields
    lender_id: Optional[AgentID] = None # Specific bank targeted
    borrower_profile: Optional[Dict[str, Any]] = None # Financial profile

    # Legacy/Spec fields
    applicant_id: Optional[AgentID] = None # Deprecated, use borrower_id
    purpose: Optional[str] = None
    term_months: Optional[int] = None # Or ticks

@dataclass
class LoanDTO:
    """
    Represents a loan, either as state or data transfer.
    Unified DTO merging LoanStateDTO and legacy LoanDTO.
    """
    loan_id: str
    borrower_id: AgentID
    principal_pennies: int
    remaining_principal_pennies: int
    interest_rate: float
    origination_tick: int

    # Unified fields
    lender_id: Optional[AgentID] = None
    due_tick: Optional[int] = None
    term_months: Optional[int] = None
    status: LoanStatus = "ACTIVE"
    is_defaulted: bool = False

@dataclass
class DepositDTO:
    """Represents a single deposit account."""
    owner_id: AgentID
    balance_pennies: int
    interest_rate: float
    deposit_id: Optional[str] = None # Added for compatibility with DepositStateDTO
    customer_id: Optional[AgentID] = None # Alias for owner_id if needed
    currency: CurrencyCode = "USD" # Default currency

# --- Phase 4.1: FX Barter DTOs ---

@dataclass
class FXMatchDTO:
    """
    Represents an atomic swap agreement between two parties.
    Used by the Matching Engine to instruct Settlement.
    """
    party_a_id: AgentID
    party_b_id: AgentID
    
    # Leg 1: A sends to B
    amount_a_pennies: int
    currency_a: CurrencyCode
    
    # Leg 2: B sends to A
    amount_b_pennies: int
    currency_b: CurrencyCode
    
    match_tick: int
    rate_a_to_b: float     # Implicit exchange rate for record keeping
