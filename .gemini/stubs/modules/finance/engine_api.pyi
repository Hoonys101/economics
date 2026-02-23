from _typeshed import Incomplete
from dataclasses import dataclass, field
from modules.finance.dtos import DepositDTO as DepositDTO, LoanApplicationDTO as LoanApplicationDTO, LoanDTO as LoanDTO
from modules.simulation.api import AgentID as AgentID
from modules.system.api import CurrencyCode as CurrencyCode, DEFAULT_CURRENCY as DEFAULT_CURRENCY
from simulation.models import Transaction as Transaction
from typing import Protocol

LoanStateDTO = LoanDTO
DepositStateDTO = DepositDTO

@dataclass
class BondStateDTO:
    bond_id: str
    owner_id: AgentID
    face_value_pennies: int
    yield_rate: float
    issue_tick: int
    maturity_tick: int

@dataclass
class BankStateDTO:
    bank_id: AgentID
    reserves: dict[CurrencyCode, int] = field(default_factory=dict)
    base_rate: float = ...
    retained_earnings_pennies: int = ...
    loans: dict[str, LoanStateDTO] = field(default_factory=dict)
    deposits: dict[str, DepositStateDTO] = field(default_factory=dict)

@dataclass
class TreasuryStateDTO:
    government_id: AgentID
    balance: dict[CurrencyCode, int] = field(default_factory=dict)
    bonds: dict[str, BondStateDTO] = field(default_factory=dict)

@dataclass
class FinancialLedgerDTO:
    """The single source of truth for financial state in the simulation."""
    current_tick: int
    banks: dict[AgentID, BankStateDTO] = field(default_factory=dict)
    treasury: TreasuryStateDTO = field(default_factory=Incomplete)

@dataclass
class EngineOutputDTO:
    updated_ledger: FinancialLedgerDTO
    generated_transactions: list[Transaction] = field(default_factory=list)

@dataclass
class LoanDecisionDTO:
    is_approved: bool
    interest_rate: float
    rejection_reason: str | None = ...

@dataclass
class LiquidationRequestDTO:
    firm_id: AgentID
    inventory_value_pennies: int
    capital_value_pennies: int
    outstanding_debt_pennies: int

class ILoanRiskEngine(Protocol):
    """(Stateless) Assesses the risk of a loan application."""
    def assess(self, application: LoanApplicationDTO, ledger: FinancialLedgerDTO) -> LoanDecisionDTO: ...

class ILoanBookingEngine(Protocol):
    """(Stateless) Books a new loan onto the ledger if approved."""
    def grant_loan(self, application: LoanApplicationDTO, decision: LoanDecisionDTO, ledger: FinancialLedgerDTO) -> EngineOutputDTO: ...

class ILiquidationEngine(Protocol):
    """(Stateless) Handles the bankruptcy and liquidation of a firm."""
    def liquidate(self, request: LiquidationRequestDTO, ledger: FinancialLedgerDTO) -> EngineOutputDTO:
        """
        Settles debts, destroys value, and generates final transactions.
        """

class IInterestRateEngine(Protocol):
    """(Stateless) Adjusts interest rates based on economic indicators."""
    def update_rates(self, economic_indicators: dict, ledger: FinancialLedgerDTO) -> FinancialLedgerDTO: ...

class IDebtServicingEngine(Protocol):
    """(Stateless) Services all active loans and bonds for a single tick."""
    def service_all_debt(self, ledger: FinancialLedgerDTO) -> EngineOutputDTO: ...
