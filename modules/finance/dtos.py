from __future__ import annotations
from typing import Dict, Optional, List, TypeAlias, Literal, Any, Union
from dataclasses import dataclass, field
from modules.simulation.api import AgentID
from modules.common.financial.dtos import MoneyDTO

CurrencyCode: TypeAlias = str
LoanStatus = Literal["PENDING", "ACTIVE", "PAID", "DEFAULTED"]

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

@dataclass(frozen=True)
class BorrowerProfileDTO:
    """
    Profile of a borrower for credit assessment.
    Updated to use AgentID and int pennies.
    """
    borrower_id: AgentID
    gross_income: int # pennies
    existing_debt_payments: int # pennies
    collateral_value: int # pennies
    credit_score: Optional[float] = None
    employment_status: str = "UNKNOWN"
    preferred_lender_id: Optional[AgentID] = None

@dataclass(frozen=True)
class LoanApplicationDTO:
    """
    Input for assessing a new loan application.
    Unified DTO merging engine_api and legacy specs.
    """
    borrower_id: AgentID
    amount_pennies: int

    # Optional fields
    lender_id: Optional[AgentID] = None # Specific bank targeted
    borrower_profile: Optional[Union[BorrowerProfileDTO, Dict[str, Any]]] = None # Financial profile

    # Legacy/Spec fields
    applicant_id: Optional[AgentID] = None # Deprecated, use borrower_id
    purpose: Optional[str] = None
    term_months: Optional[int] = None # Or ticks

@dataclass
class LoanDTO:
    """
    Represents a loan, either as state or data transfer.
    Unified DTO merging LoanStateDTO and legacy LoanDTO.
    Replaces LoanInfoDTO.
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
    term_ticks: Optional[int] = None # Replaces term_months in legacy LoanInfoDTO context
    term_months: Optional[int] = None # Kept for legacy compatibility if needed
    status: LoanStatus = "ACTIVE"
    is_defaulted: bool = False

    # Legacy Alias Properties (Read-Only) to ease transition from LoanInfoDTO
    @property
    def original_amount(self) -> float:
        return float(self.principal_pennies) / 100.0

    @property
    def outstanding_balance(self) -> float:
        return float(self.remaining_principal_pennies) / 100.0

@dataclass
class DepositDTO:
    """Represents a single deposit account."""
    owner_id: AgentID
    balance_pennies: int
    interest_rate: float
    deposit_id: Optional[str] = None # Added for compatibility with DepositStateDTO
    customer_id: Optional[AgentID] = None # Alias for owner_id if needed
    currency: CurrencyCode = "USD" # Default currency

@dataclass(frozen=True)
class BailoutCovenant:
    """
    Restrictions applied to a bailout loan.
    """
    dividends_allowed: bool = False
    executive_bonus_allowed: bool = False
    min_employment_level: Optional[int] = None

@dataclass
class BailoutLoanDTO:
    """Data Transfer Object for corporate bailout loans."""
    firm_id: AgentID
    amount: int
    interest_rate: float
    covenants: BailoutCovenant

@dataclass(frozen=True)
class GrantBailoutCommand:
    """
    Command to grant a bailout loan to a distressed entity.
    """
    firm_id: AgentID
    amount: float
    interest_rate: float
    covenants: BailoutCovenant

@dataclass(frozen=True)
class SettlementOrder:
    """A command to execute a monetary transfer via the SettlementSystem."""
    sender_id: AgentID
    receiver_id: AgentID
    amount_pennies: int
    currency: CurrencyCode
    memo: str
    transaction_type: str # e.g., 'WAGE', 'TAX', 'PURCHASE', 'ASSET_ENDOWMENT'

@dataclass(frozen=True)
class TaxCollectionResult:
    """
    Represents the verified outcome of a tax collection attempt.
    """
    success: bool
    amount_collected: int
    tax_type: str
    payer_id: AgentID
    payee_id: AgentID
    error_message: Optional[str]

@dataclass
class BondDTO:
    """Data Transfer Object for government bonds."""
    id: str
    issuer: str
    face_value: int # pennies
    yield_rate: float
    maturity_date: int

@dataclass(frozen=True)
class PortfolioAsset:
    """Represents a single type of asset holding."""
    asset_type: str  # e.g., 'stock', 'bond'
    asset_id: str    # e.g., 'FIRM_1', 'GOV_BOND_10Y'
    quantity: float

@dataclass(frozen=True)
class PortfolioDTO:
    """A comprehensive, serializable representation of an agent's portfolio."""
    assets: List[PortfolioAsset]

@dataclass(frozen=True)
class LienDTO:
    """
    Represents a financial claim (lien) against a real estate property.
    This is the canonical data structure for all property-secured debt.
    """
    loan_id: str
    lienholder_id: AgentID  # The ID of the agent/entity holding the lien (e.g., the bank)
    principal_remaining: int # pennies
    lien_type: Literal["MORTGAGE", "TAX_LIEN", "JUDGEMENT_LIEN"]

@dataclass(frozen=True)
class MortgageApplicationDTO:
    """
    Application data for a mortgage.
    """
    applicant_id: AgentID
    requested_principal: int # pennies
    purpose: str
    property_id: int
    property_value: int # pennies
    applicant_monthly_income: int # pennies
    existing_monthly_debt_payments: int # pennies
    loan_term: int # ticks

@dataclass(frozen=True)
class CreditAssessmentResultDTO:
    """
    The result of a credit check from the CreditScoringService.
    """
    is_approved: bool
    max_loan_amount: int # pennies
    reason: Optional[str] # Reason for denial

@dataclass(frozen=True)
class EquityStake:
    """Represents a shareholder's stake for Tier 5 distribution."""
    shareholder_id: AgentID
    ratio: float # Proportional ownership, e.g., 0.1 for 10%

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

@dataclass(frozen=True)
class DebtStatusDTO:
    """Module A: Hardened financial debt representation (Pennies only)."""
    borrower_id: AgentID
    total_outstanding_pennies: int
    loans: List[LoanDTO]
    is_insolvent: bool
    next_payment_pennies: int
    next_payment_tick: int
