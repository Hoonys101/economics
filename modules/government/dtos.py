from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union, Protocol, runtime_checkable, TYPE_CHECKING
from simulation.ai.enums import PolicyActionTag
from modules.system.api import CurrencyCode
from modules.finance.api import BailoutLoanDTO, BondDTO

# region: Type Definitions
@runtime_checkable
class IAgent(Protocol):
    id: int

FirmID = int
HouseholdID = int
# endregion

# region: Existing DTOs
@dataclass
class TaxHistoryItemDTO:
    tick: int
    total: int # MIGRATION: pennies
    tax_revenue: Dict[str, int] # MIGRATION: pennies

@dataclass
class TaxBracketDTO:
    """Defines a single progressive tax bracket."""
    threshold: int # Pennies (replaces floor)
    rate: float
    # Deprecated fields for compatibility
    floor: int = 0
    ceiling: Optional[int] = None

@dataclass
class FiscalPolicyDTO:
    """Defines the government's fiscal stance including tax rates and brackets."""
    tax_brackets: List[TaxBracketDTO]
    income_tax_rate: float
    corporate_tax_rate: float
    vat_rate: float = 0.0

@dataclass(frozen=True)
class FiscalPolicyDTO:
    """Snapshot of the current fiscal policy."""
    income_tax_rate: float
    corporate_tax_rate: float
    tax_brackets: List[TaxBracketDTO] = field(default_factory=list)
    welfare_budget_multiplier: float = 1.0
    vat_rate: float = 0.0

@dataclass(frozen=True)
class GovernmentPolicyDTO:
    """
    Unified Policy Snapshot for the Government.
    Consolidates Fiscal and Monetary stances for atomic state transfer.
    """
    # Fiscal Policy
    tax_brackets: List[TaxBracketDTO] = field(default_factory=list)
    corporate_tax_rate: float = 0.2
    income_tax_rate: float = 0.1
    vat_rate: float = 0.0
    
    # Monetary Policy (Snapshot)
    target_interest_rate: float = 0.05
    inflation_target: float = 0.02
    unemployment_target: float = 0.05
    
    # Welfare & Bailout
    welfare_budget_multiplier: float = 1.0
    bailout_threshold_solvency: float = 0.1

@dataclass
class MonetaryPolicyDTO:
    """State of the current monetary policy."""
    target_interest_rate: float
    inflation_target: float
    unemployment_target: float
    # TBD: QE/QT parameters

@dataclass
class GovernmentStateDTO:
    """Immutable snapshot of the Government's state."""
    tick: int
    assets: Dict[str, int] # MIGRATION: pennies
    total_debt: int # MIGRATION: pennies
    income_tax_rate: float
    corporate_tax_rate: float
    # Removed duplicate fields
    policy: GovernmentPolicyDTO
    fiscal_policy: Optional[FiscalPolicyDTO] # Explicit fiscal policy
    approval_rating: float
    policy_lockouts: Dict[Any, int] = field(default_factory=dict) # <PolicyActionTag, locked_until_tick>
    sensory_data: Optional[GovernmentSensoryDTO] = None
    gdp_history: List[float] = field(default_factory=list)
    welfare_budget_multiplier: float = 1.0
    potential_gdp: float = 0.0
    fiscal_stance: float = 0.0
    welfare_budget_multiplier: float = 1.0

@dataclass
class PolicyDecisionDTO:
    """High-level strategic decision from the DecisionEngine."""
    action_tag: Any # e.g., PolicyActionTag Enum
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "OK"

@dataclass
class ExecutionResultDTO:
    """Concrete commands resulting from policy execution."""
    payment_requests: List['PaymentRequestDTO'] = field(default_factory=list)
    bailout_results: List['BailoutResultDTO'] = field(default_factory=list)
    monetary_ledger_updates: Dict[str, int] = field(default_factory=dict) # MIGRATION: pennies
    state_updates: Dict[str, Any] = field(default_factory=dict) # For Orchestrator to update its state
    transactions: List[Any] = field(default_factory=list) # General transactions (e.g. from bailouts)
    executed_loans: List[Any] = field(default_factory=list) # Executed loan objects (e.g. from bailouts)

@dataclass
class MacroEconomicSnapshotDTO:
    """Snapshot of macro-economic indicators for Monetary Policy."""
    inflation_rate: float
    nominal_gdp: float
    potential_gdp: float
    unemployment_rate: float

@dataclass
class PolicyActionDTO:
    """Represents a proposed government policy action."""
    name: str
    utility: float
    tag: PolicyActionTag
    action_type: str
    params: Dict[str, Any] = field(default_factory=dict)
# endregion

# region: NEW & REVISED DTOs for Decoupling (TD-300)

@dataclass
class FiscalContextDTO:
    """Context for fiscal operations (Tax, Bonds)."""
    tick: int
    current_gdp: int # Pennies
    debt_to_gdp_ratio: float
    population_count: int
    treasury_balance: int # Pennies

@dataclass
class BondIssueRequestDTO:
    """Request to issue bonds."""
    amount_pennies: int
    maturity_ticks: int
    target_yield: float
    # Optional: Buyer specific info if known, but usually market or specific bank/CB

@dataclass
class PaymentRequestDTO:
    """
    A stateless request for a financial transfer.
    Generated by a service, executed by the agent holding the wallet.
    """
    payer: Union[IAgent, FirmID, HouseholdID, str] # Supports "GOVERNMENT" string
    payee: Union[IAgent, FirmID, HouseholdID, str]
    amount: int # MIGRATION: pennies
    currency: CurrencyCode
    memo: str

@dataclass
class BondIssuanceResultDTO:
    """Result of bond issuance preparation."""
    payment_request: PaymentRequestDTO
    bond_dto: BondDTO

@dataclass
class TaxAssessmentResultDTO:
    """Result from a tax assessment operation, containing payment requests."""
    payment_requests: List[PaymentRequestDTO] = field(default_factory=list)
    total_collected: int = 0 # MIGRATION: pennies
    tax_type: str = ""

@dataclass
class WelfareResultDTO:
    """Result from a welfare check operation, containing payment requests."""
    payment_requests: List[PaymentRequestDTO] = field(default_factory=list)
    total_paid: int = 0 # MIGRATION: pennies

@dataclass
class BailoutResultDTO:
    """
    Result from a bailout evaluation, requesting the creation of a loan
    and the initial fund transfer.
    """
    loan_request: BailoutLoanDTO # The DTO defining the loan terms
    payment_request: PaymentRequestDTO # The initial transfer of funds

@dataclass(frozen=True)
class BondRepaymentDetailsDTO:
    """
    A structured object carrying the details of a bond repayment.
    This DTO is expected to be present in the 'metadata' field of a 'bond_repayment' Transaction.

    Attributes:
        principal_pennies: The portion of the payment that constitutes principal repayment.
                           This amount is subject to monetary destruction if paid to the Central Bank.
        interest_pennies: The portion of the payment that constitutes an interest payment.
                          This is treated as a standard transfer and is not destroyed.
        bond_id: A unique identifier for the bond being serviced.
    """
    principal_pennies: int
    interest_pennies: int
    bond_id: str

# endregion

@dataclass
@dataclass
class GovernmentSensoryDTO:
    """
    WO-057-B: Sensory Module DTO.
    Transfers 10-tick SMA macro data to the Government Agent.
    """
    tick: int
    inflation_sma: float
    unemployment_sma: float
    gdp_growth_sma: float
    wage_sma: float
    approval_sma: float
    current_gdp: float
    # WO-057-A: Added for AdaptiveGovBrain
    gini_index: float = 0.0
    approval_low_asset: float = 0.5
    approval_high_asset: float = 0.5
