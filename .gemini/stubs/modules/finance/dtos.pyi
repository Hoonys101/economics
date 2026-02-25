from _typeshed import Incomplete
from dataclasses import dataclass, field as field
from modules.common.financial.dtos import MoneyDTO as MoneyDTO
from modules.simulation.api import AgentID as AgentID
from typing import Any, Literal, TypeAlias

CurrencyCode: TypeAlias = str
LoanStatus: Incomplete

@dataclass
class MultiCurrencyWalletDTO:
    """Represents a complete portfolio of assets, keyed by currency."""
    balances: dict[CurrencyCode, int]

@dataclass
class InvestmentOrderDTO:
    """Defines an internal order for investment (e.g., R&D, Capex)."""
    order_type: str
    investment: MoneyDTO
    target_agent_id: AgentID | None = ...

@dataclass(frozen=True)
class BorrowerProfileDTO:
    """
    Profile of a borrower for credit assessment.
    Updated to use AgentID and int pennies.
    """
    borrower_id: AgentID
    gross_income: int
    existing_debt_payments: int
    collateral_value: int
    credit_score: float | None = ...
    employment_status: str = ...
    preferred_lender_id: AgentID | None = ...

@dataclass(frozen=True)
class LoanApplicationDTO:
    """
    Input for assessing a new loan application.
    Unified DTO merging engine_api and legacy specs.
    """
    borrower_id: AgentID
    amount_pennies: int
    lender_id: AgentID | None = ...
    borrower_profile: BorrowerProfileDTO | dict[str, Any] | None = ...
    applicant_id: AgentID | None = ...
    purpose: str | None = ...
    term_months: int | None = ...

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
    lender_id: AgentID | None = ...
    due_tick: int | None = ...
    term_ticks: int | None = ...
    term_months: int | None = ...
    status: LoanStatus = ...
    is_defaulted: bool = ...
    @property
    def original_amount(self) -> float: ...
    @property
    def outstanding_balance(self) -> float: ...

@dataclass
class DepositDTO:
    """Represents a single deposit account."""
    owner_id: AgentID
    balance_pennies: int
    interest_rate: float
    deposit_id: str | None = ...
    customer_id: AgentID | None = ...
    currency: CurrencyCode = ...

@dataclass(frozen=True)
class BailoutCovenant:
    """
    Restrictions applied to a bailout loan.
    """
    dividends_allowed: bool = ...
    executive_bonus_allowed: bool = ...
    min_employment_level: int | None = ...

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
    transaction_type: str

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
    error_message: str | None

@dataclass
class BondDTO:
    """Data Transfer Object for government bonds."""
    id: str
    issuer: str
    face_value: int
    yield_rate: float
    maturity_date: int

@dataclass(frozen=True)
class PortfolioAsset:
    """Represents a single type of asset holding."""
    asset_type: str
    asset_id: str
    quantity: float

@dataclass(frozen=True)
class PortfolioDTO:
    """A comprehensive, serializable representation of an agent's portfolio."""
    assets: list[PortfolioAsset]

@dataclass(frozen=True)
class LienDTO:
    """
    Represents a financial claim (lien) against a real estate property.
    This is the canonical data structure for all property-secured debt.
    """
    loan_id: str
    lienholder_id: AgentID
    principal_remaining: int
    lien_type: Literal['MORTGAGE', 'TAX_LIEN', 'JUDGEMENT_LIEN']

@dataclass(frozen=True)
class MortgageApplicationDTO:
    """
    Application data for a mortgage.
    """
    applicant_id: AgentID
    requested_principal: int
    purpose: str
    property_id: int
    property_value: int
    applicant_monthly_income: int
    existing_monthly_debt_payments: int
    loan_term: int

@dataclass(frozen=True)
class CreditAssessmentResultDTO:
    """
    The result of a credit check from the CreditScoringService.
    """
    is_approved: bool
    max_loan_amount: int
    reason: str | None

@dataclass(frozen=True)
class EquityStake:
    """Represents a shareholder's stake for Tier 5 distribution."""
    shareholder_id: AgentID
    ratio: float

@dataclass
class FXMatchDTO:
    """
    Represents an atomic swap agreement between two parties.
    Used by the Matching Engine to instruct Settlement.
    """
    party_a_id: AgentID
    party_b_id: AgentID
    amount_a_pennies: int
    currency_a: CurrencyCode
    amount_b_pennies: int
    currency_b: CurrencyCode
    match_tick: int
    rate_a_to_b: float

@dataclass(frozen=True)
class DebtStatusDTO:
    """Module A: Hardened financial debt representation (Pennies only)."""
    borrower_id: AgentID
    total_outstanding_pennies: int
    loans: list[LoanDTO]
    is_insolvent: bool
    next_payment_pennies: int
    next_payment_tick: int
