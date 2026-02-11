from typing import TypedDict, List, Dict, Optional, Protocol, runtime_checkable
from dataclasses import dataclass, field

from modules.simulation.api import AgentID
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY
from simulation.models import Transaction

# =================================================================
# 1. CORE STATE DTOs (The Financial Ledger)
# =================================================================

# Represents a single loan on the books
@dataclass
class LoanStateDTO:
    loan_id: str
    borrower_id: AgentID
    lender_id: AgentID # e.g., Bank ID
    principal: float
    remaining_principal: float
    interest_rate: float
    origination_tick: int
    due_tick: int
    is_defaulted: bool = False

# Represents a single deposit account
@dataclass
class DepositStateDTO:
    deposit_id: str
    customer_id: AgentID
    balance: float
    interest_rate: float
    currency: CurrencyCode = DEFAULT_CURRENCY

# Represents a government bond
@dataclass
class BondStateDTO:
    bond_id: str
    owner_id: AgentID # Who holds the bond (e.g., Bank, CentralBank)
    face_value: float
    yield_rate: float
    issue_tick: int
    maturity_tick: int

# State specific to the banking system
@dataclass
class BankStateDTO:
    bank_id: AgentID
    reserves: Dict[CurrencyCode, float] = field(default_factory=dict)
    base_rate: float = 0.03
    retained_earnings: float = 0.0 # Tracks internal equity/profits
    loans: Dict[str, LoanStateDTO] = field(default_factory=dict) # Key: loan_id
    deposits: Dict[str, DepositStateDTO] = field(default_factory=dict) # Key: deposit_id

# State specific to government treasury and debt
@dataclass
class TreasuryStateDTO:
    government_id: AgentID
    balance: Dict[CurrencyCode, float] = field(default_factory=dict)
    bonds: Dict[str, BondStateDTO] = field(default_factory=dict) # Key: bond_id

# The central, unified ledger for all financial state
@dataclass
class FinancialLedgerDTO:
    """The single source of truth for financial state in the simulation."""
    current_tick: int
    banks: Dict[AgentID, BankStateDTO] = field(default_factory=dict)
    treasury: TreasuryStateDTO = field(default_factory=lambda: TreasuryStateDTO(government_id="GOVERNMENT"))
    # Add other major financial entities here if needed (e.g., CentralBankState)

# =================================================================
# 2. INPUT/OUTPUT DTOs for Engines
# =================================================================

# Result from any engine operation
@dataclass
class EngineOutputDTO:
    updated_ledger: FinancialLedgerDTO
    generated_transactions: List[Transaction] = field(default_factory=list)

# Input for assessing a new loan application
@dataclass
class LoanApplicationDTO:
    borrower_id: AgentID
    lender_id: AgentID # Specific bank targeted
    amount: float
    # Borrower financial profile, credit score, etc.
    # To be defined, but let's assume it's a dict for now
    borrower_profile: Dict

# Decision from the risk assessment engine
@dataclass
class LoanDecisionDTO:
    is_approved: bool
    interest_rate: float
    rejection_reason: Optional[str] = None

# Input for firm liquidation
@dataclass
class LiquidationRequestDTO:
    firm_id: AgentID
    inventory_value: float
    capital_value: float
    outstanding_debt: float # Total debt to be settled

# =================================================================
# 3. STATELESS ENGINE INTERFACES (Protocols)
# =================================================================

@runtime_checkable
class ILoanRiskEngine(Protocol):
    """(Stateless) Assesses the risk of a loan application."""
    def assess(
        self,
        application: LoanApplicationDTO,
        ledger: FinancialLedgerDTO # For context (e.g., current base rates)
    ) -> LoanDecisionDTO:
        ...

@runtime_checkable
class ILoanBookingEngine(Protocol):
    """(Stateless) Books a new loan onto the ledger if approved."""
    def grant_loan(
        self,
        application: LoanApplicationDTO,
        decision: LoanDecisionDTO,
        ledger: FinancialLedgerDTO
    ) -> EngineOutputDTO:
        ...

@runtime_checkable
class ILiquidationEngine(Protocol):
    """(Stateless) Handles the bankruptcy and liquidation of a firm."""
    def liquidate(
        self,
        request: LiquidationRequestDTO,
        ledger: FinancialLedgerDTO
    ) -> EngineOutputDTO:
        """
        Settles debts, destroys value, and generates final transactions.
        """
        ...

@runtime_checkable
class IInterestRateEngine(Protocol):
    """(Stateless) Adjusts interest rates based on economic indicators."""
    def update_rates(
        self,
        # Economic indicators (GDP, CPI, etc.) would be passed here
        economic_indicators: Dict,
        ledger: FinancialLedgerDTO
    ) -> FinancialLedgerDTO: # Returns only the updated ledger
        ...

@runtime_checkable
class IDebtServicingEngine(Protocol):
    """(Stateless) Services all active loans and bonds for a single tick."""
    def service_all_debt(self, ledger: FinancialLedgerDTO) -> EngineOutputDTO:
        ...
