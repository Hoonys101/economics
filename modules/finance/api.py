from __future__ import annotations
from typing import Protocol, Dict, List, Any, Optional, TypedDict, Literal, Tuple, runtime_checkable, TYPE_CHECKING, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import abc
from abc import ABC, abstractmethod
from uuid import UUID
from modules.finance.dtos import MoneyDTO, MultiCurrencyWalletDTO, LoanApplicationDTO, LoanDTO, DepositDTO, FXMatchDTO
from modules.system.api import MarketContextDTO, DEFAULT_CURRENCY, CurrencyCode
from modules.simulation.api import AgentID, AnyAgentID

@runtime_checkable
class ITransaction(Protocol):
    """Module A: Protocol for a completed financial transaction."""
    sender_id: AgentID
    receiver_id: AgentID
    amount_pennies: int
    tick: int
    transaction_type: str
    memo: Optional[str] = None

if TYPE_CHECKING:
    from modules.simulation.api import IGovernment, EconomicIndicatorsDTO
    from simulation.dtos.api import GovernmentSensoryDTO
    from simulation.models import Order, Transaction
    from modules.common.dtos import Claim
    from modules.finance.wallet.api import IWallet
    from modules.hr.api import IHRService
    from modules.finance.engine_api import BankStateDTO, DepositStateDTO, LoanStateDTO

# Forward reference for type hinting
class Firm: pass
class Household: pass # Assuming Household agent also interacts with the bank

@runtime_checkable
class IConfig(Protocol):
    """Protocol for configuration module."""
    def get(self, key: str, default: Any = None) -> Any: ...

@runtime_checkable
class IFinancialEntity(Protocol):
    """
    Standard interface for any entity capable of holding and transferring financial value.
    Replaces legacy `hasattr` checks and standardizes on integer pennies.
    """
    @property
    def balance_pennies(self) -> int:
        """Returns the balance in the default currency (pennies)."""
        ...

    def deposit(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Deposits funds into the entity's wallet."""
        ...

    def withdraw(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Withdraws funds from the entity's wallet."""
        ...

@runtime_checkable
class IFinancialFirm(IFinancialEntity, Protocol):
    """
    Interface for a Firm entity used in financial analysis (e.g., Solvency).
    Ensures strict typing for solvency checks and financial reporting.
    """
    id: AgentID

    @property
    def age(self) -> int:
        """The age of the firm in ticks."""
        ...

    @age.setter
    def age(self, value: int) -> None:
        ...

    @property
    def capital_stock_units(self) -> int:
        """The capital stock quantity in units."""
        ...

    @property
    def inventory_value_pennies(self) -> int:
        """The total value of inventory in pennies."""
        ...

    @property
    def monthly_wage_bill_pennies(self) -> int:
        """The total monthly wage bill in pennies."""
        ...

    @property
    def total_debt_pennies(self) -> int:
        """The total outstanding debt in pennies."""
        ...

    @property
    def retained_earnings_pennies(self) -> int:
        """The retained earnings in pennies."""
        ...

    @property
    def average_profit_pennies(self) -> int:
        """The average profit over the relevant history in pennies."""
        ...

@runtime_checkable
class IFinanceDepartment(Protocol):
    """
    Interface for a Firm's financial operations, designed for a multi-currency environment.
    MIGRATION: All monetary values are integers (pennies).
    """

    @property
    @abstractmethod
    def balance(self) -> Dict[CurrencyCode, int]:
        """Provides direct access to the raw balances dict."""
        ...

    @abstractmethod
    def get_balance(self, currency: CurrencyCode) -> int:
        """Gets the balance for a specific currency."""
        ...

    @abstractmethod
    def deposit(self, amount: int, currency: CurrencyCode):
        """Deposits a specific amount of a given currency."""
        ...

    @abstractmethod
    def withdraw(self, amount: int, currency: CurrencyCode):
        """Withdraws a specific amount of a given currency. Raises InsufficientFundsError if needed."""
        ...

    @abstractmethod
    def get_financial_snapshot(self) -> Dict[str, Union[MoneyDTO, MultiCurrencyWalletDTO, float]]:
        """Returns a comprehensive, currency-aware snapshot of the firm's financials."""
        ...

    @abstractmethod
    def calculate_valuation(self, market_context: MarketContextDTO) -> MoneyDTO:
        """
        Calculates the firm's total valuation, converted to its primary currency.
        Requires current market context.
        """
        ...

    @abstractmethod
    def generate_financial_transactions(
        self,
        government: Any,
        all_households: List[Any],
        current_time: int,
        market_context: MarketContextDTO
    ) -> List[Any]: # Returns List[Transaction]
        """
        Generates all standard financial transactions (taxes, dividends, maintenance)
        in a currency-aware manner.
        """
        ...

    @abstractmethod
    def set_dividend_rate(self, new_rate: float) -> None:
        """Sets the dividend rate."""
        ...

    @abstractmethod
    def pay_ad_hoc_tax(self, amount: int, currency: CurrencyCode, reason: str, government: Any, current_time: int) -> None:
        """Pays a one-time tax of a specific currency."""
        ...

@dataclass
class BondDTO:
    """Data Transfer Object for government bonds."""
    id: str
    issuer: str
    face_value: int
    yield_rate: float
    maturity_date: int

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

# --- Portfolio DTOs (TD-160) ---

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

@dataclass(frozen=True)
class LoanInfoDTO:
    """
    Data Transfer Object for Loan Information.
    Strictly used for passing loan data across boundaries.
    """
    loan_id: str
    borrower_id: int  # AgentID
    original_amount: float
    outstanding_balance: float
    interest_rate: float
    origination_tick: int
    due_tick: int
    lender_id: Optional[int] = None
    term_ticks: Optional[int] = None
    status: str = "ACTIVE"

@dataclass(frozen=True)
class DebtStatusDTO:
    """Module A: Hardened financial debt representation (Pennies only)."""
    borrower_id: AgentID
    total_outstanding_pennies: int
    loans: List[LoanInfoDTO]
    is_insolvent: bool
    next_payment_pennies: int
    next_payment_tick: int

class InsufficientFundsError(Exception):
    """
    Custom exception to be raised when an operation cannot be completed due to lack of funds.
    """
    def __init__(self, message: str, required: Optional[MoneyDTO] = None, available: Optional[MoneyDTO] = None):
        self.required = required
        self.available = available
        if required and available:
             msg = f"{message} Required: {required['amount_pennies']} pennies {required['currency']}, Available: {available['amount_pennies']} pennies {available['currency']}"
        else:
             msg = message
        super().__init__(msg)

class LoanNotFoundError(Exception):
    """Raised when a specified loan is not found."""
    pass

class LoanRepaymentError(Exception):
    """Raised when there is an issue with loan repayment."""
    pass

class LoanRollbackError(Exception):
    """Raised when a loan cancellation fails to reverse the associated deposit."""
    pass

@dataclass(frozen=True)
class BorrowerProfileDTO:
    """
    Profile of a borrower for credit assessment.
    Updated: Added borrower_id to resolve TD-DTO-DESYNC-2026.
    """
    borrower_id: AgentID  # Added to resolve signature desync
    gross_income: float
    existing_debt_payments: float
    collateral_value: float
    credit_score: Optional[float] = None
    employment_status: str = "UNKNOWN"
    preferred_lender_id: Optional[int] = None

@dataclass(frozen=True)
class CreditAssessmentResultDTO:
    """
    The result of a credit check from the CreditScoringService.
    """
    is_approved: bool
    max_loan_amount: int
    reason: Optional[str] # Reason for denial

# --- Lien and Encumbrance DTOs ---

@dataclass(frozen=True)
class LienDTO:
    """
    Represents a financial claim (lien) against a real estate property.
    This is the canonical data structure for all property-secured debt.
    """
    loan_id: str
    lienholder_id: AgentID  # The ID of the agent/entity holding the lien (e.g., the bank)
    principal_remaining: int
    lien_type: Literal["MORTGAGE", "TAX_LIEN", "JUDGEMENT_LIEN"]

@dataclass(frozen=True)
class MortgageApplicationDTO:
    """
    Application data for a mortgage.
    TypedDict allows for flexible input construction before strict validation.
    """
    applicant_id: int
    requested_principal: float
    purpose: str
    property_id: int
    property_value: float
    applicant_monthly_income: float
    existing_monthly_debt_payments: float
    loan_term: int

@runtime_checkable
class ICreditScoringService(Protocol):
    """
    Interface for a service that assesses the creditworthiness of a potential borrower.
    """

    @abc.abstractmethod
    def assess_creditworthiness(self, profile: BorrowerProfileDTO, requested_loan_amount: int) -> CreditAssessmentResultDTO:
        """
        Evaluates a borrower's financial profile against lending criteria.

        Args:
            profile: A DTO containing the borrower's financial information.
            requested_loan_amount: The amount of the loan being requested.

        Returns:
            A DTO indicating approval status and other relevant details.
        """
        ...

@dataclass(frozen=True)
class EquityStake:
    """Represents a shareholder's stake for Tier 5 distribution."""
    shareholder_id: AgentID
    ratio: float # Proportional ownership, e.g., 0.1 for 10%

@dataclass(frozen=True)
class LiquidationContext:
    """Context object to supply necessary services for claim calculation."""
    current_tick: int
    hr_service: Optional[IHRService] = None
    tax_service: Optional[Union[ITaxService, Any]] = None # Use Union[ITaxService, Any] to avoid forward ref issue if ITaxService not defined yet or use string
    shareholder_registry: Optional[IShareholderRegistry] = None

@runtime_checkable
class ILiquidatable(Protocol):
    """
    An interface for any entity that can undergo a formal liquidation process.
    Provides all necessary financial claims and asset information to a liquidator.
    """
    id: AgentID

    def liquidate_assets(self, current_tick: int) -> Dict[CurrencyCode, int]:
        """
        Performs internal write-offs of non-cash assets (inventory, capital)
        and returns a dictionary of all remaining cash-equivalent assets by currency.
        This signals the final step before cash distribution begins.
        """
        ...

    def get_all_claims(self, ctx: LiquidationContext) -> List[Claim]:
        """
        Aggregates all non-equity claims (HR, Tax, Debt) against the entity.
        The implementation is responsible for determining the amounts and creditors.
        """
        ...

    def get_equity_stakes(self, ctx: LiquidationContext) -> List[EquityStake]:
        """
        Returns a list of all shareholders and their proportional stake for Tier 5 distribution.
        An empty list signifies no equity holders.
        """
        ...

@runtime_checkable
class IFinancialAgent(Protocol):
    """
    Protocol for agents participating in the financial system.
    """
    id: AgentID

    def get_liquid_assets(self, currency: CurrencyCode = "USD") -> float:
        ...

    def get_total_debt(self) -> float:
        ...

    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Deposits a specific amount of a given currency. Internal use only."""
        ...

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        Withdraws a specific amount of a given currency.
        Raises InsufficientFundsError if funds are insufficient.
        Internal use only.
        """
        ...

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        """Returns the current balance for the specified currency."""
        ...

    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        """Returns a copy of all currency balances."""
        ...

    @property
    def total_wealth(self) -> int:
        """Returns the total wealth in default currency estimation."""
        ...

@runtime_checkable
class IBankService(Protocol):
    """
    Interface for Bank Services used by Markets.
    """
    def get_interest_rate(self) -> float: ...

    def grant_loan(self, borrower_id: int, amount: int, interest_rate: float, due_tick: int) -> Optional[Tuple[LoanInfoDTO, Any]]: ...

    def stage_loan(self, borrower_id: int, amount: int, interest_rate: float, due_tick: Optional[int], borrower_profile: Optional[BorrowerProfileDTO]) -> Optional[LoanInfoDTO]: ...

    def repay_loan(self, loan_id: str, amount: int) -> int: ...

@runtime_checkable
class IBank(IBankService, IFinancialEntity, IFinancialAgent, Protocol):
    """
    Interface for commercial and central banks, providing core banking services.
    Designed to be used as a dependency for Household and Firm agents.
    Inherits IFinancialAgent for its own equity/reserves management.
    """
    base_rate: float

    @abc.abstractmethod
    def get_customer_balance(self, agent_id: AgentID) -> int:
        """
        Retrieves the current balance for a given CUSTOMER account (deposit).
        Use get_balance(currency) for the Bank's own funds.
        """
        ...

    @abc.abstractmethod
    def get_debt_status(self, borrower_id: AgentID) -> DebtStatusDTO:
        """
        Retrieves the comprehensive debt status for a given borrower.
        """
        ...

    @abc.abstractmethod
    def terminate_loan(self, loan_id: str) -> Optional["Transaction"]:
        """
        Forcefully terminates a loan (e.g. foreclosure or voiding).
        """
        ...

    @abc.abstractmethod
    def withdraw_for_customer(self, agent_id: AgentID, amount: int) -> bool:
        """
        Withdraws funds from a customer's deposit account.
        """
        ...

    @abc.abstractmethod
    def get_total_deposits(self) -> int:
        """
        Returns the sum of all customer deposits held by the bank.
        """
        ...

    @abc.abstractmethod
    def close_account(self, agent_id: AgentID) -> int:
        """
        Closes the deposit account for the agent and returns the final balance.
        """
        ...

    @abc.abstractmethod
    def repay_loan(self, loan_id: str, amount: int) -> int:
        """
        Records a repayment for a specific loan. Returns the amount applied.
        This method updates the ledger but does NOT transfer funds.
        """
        ...

    @abc.abstractmethod
    def receive_repayment(self, borrower_id: AgentID, amount: int) -> int:
        """
        Receives a generic repayment from a borrower and applies it to outstanding debt.
        Returns the total amount applied.
        """
        ...

# IBankService = IBank # Removed alias

@runtime_checkable
class IFiscalMonitor(Protocol):
    """Interface for the fiscal health analysis component."""
    def get_debt_to_gdp_ratio(self, government: "IGovernment", indicators: "EconomicIndicatorsDTO") -> float: ...

@runtime_checkable
class IGovernmentFinance(IFinancialAgent, Protocol):
    """Interface for Government interaction within FinanceSystem."""
    total_debt: int
    sensory_data: Optional[GovernmentSensoryDTO]

@runtime_checkable
class IBankRegistry(Protocol):
    """
    Module A: Interface for the Bank Account Directory Service.
    Decouples account lookup from transaction settlement.
    """
    def register_account(self, bank_id: int, agent_id: int) -> None:
        """Registers an account link between a bank and an agent."""
        ...

    def deregister_account(self, bank_id: int, agent_id: int) -> None:
        """Removes an account link between a bank and an agent."""
        ...

    def get_account_holders(self, bank_id: int) -> List[int]:
        """Returns a list of all agents holding accounts at the specified bank."""
        ...

    def get_agent_banks(self, agent_id: int) -> List[int]:
        """Returns a list of banks where the agent holds an account."""
        ...

    def remove_agent_from_all_accounts(self, agent_id: int) -> None:
        """Removes an agent from all bank account indices."""
        ...

@runtime_checkable
class ISettlementSystem(IBankRegistry, Protocol):
    """
    Interface for the centralized settlement system.
    Basic financial operations for Households and Firms.
    Inherits IBankRegistry to maintain backward compatibility for account management
    methods during the transition to a dedicated BankRegistry service.
    """

    def transfer(
        self,
        debit_agent: IFinancialAgent,
        credit_agent: IFinancialAgent,
        amount: int,
        memo: str,
        debit_context: Optional[Dict[str, Any]] = None,
        credit_context: Optional[Dict[str, Any]] = None,
        tick: int = 0,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> Optional[ITransaction]:
        """Executes an immediate, single transfer. Returns transaction or None."""
        ...

    def execute_swap(self, match: FXMatchDTO) -> Optional[ITransaction]:
        """
        Phase 4.1: Executes an atomic currency swap (Barter FX).
        Ensures both legs (A->B, B->A) succeed or neither occurs.
        """
        ...

    def get_balance(self, agent_id: AgentID, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        """
        Queries the Single Source of Truth for an agent's current balance.
        This is the ONLY permissible way to check another agent's funds.
        """
        ...

@runtime_checkable
class IMonetaryAuthority(ISettlementSystem, Protocol):
    """
    Interface for monetary authority operations (Central Bank, Government, God Mode).
    Extends ISettlementSystem with money creation/destruction capabilities.
    """

    def create_and_transfer(
        self,
        source_authority: IFinancialAgent,
        destination: IFinancialAgent,
        amount: int,
        reason: str,
        tick: int,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> Optional[ITransaction]:
        """Creates new money (or grants) and transfers it to an agent."""
        ...

    def transfer_and_destroy(
        self,
        source: IFinancialAgent,
        sink_authority: IFinancialAgent,
        amount: int,
        reason: str,
        tick: int,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> Optional[ITransaction]:
        """Transfers money from an agent to an authority to be destroyed."""
        ...

    def mint_and_distribute(self, target_agent_id: int, amount: int, tick: int = 0, reason: str = "god_mode_injection") -> bool:
        """Minting capability for God Mode."""
        ...

    def audit_total_m2(self, expected_total: Optional[int] = None) -> bool:
        """
        Audits the total M2 money supply in the system.
        Returns True if the audit passes (or no expectation set), False otherwise.
        """
        ...

    def record_liquidation(
        self,
        agent: IFinancialAgent,
        inventory_value: int,
        capital_value: int,
        recovered_cash: int,
        reason: str,
        tick: int,
        government_agent: Optional[IFinancialAgent] = None
    ) -> None:
        """
        Records the outcome of an asset liquidation.
        """
        ...

@runtime_checkable
class IFinanceSystem(Protocol):
    """Interface for the sovereign debt and corporate bailout system."""

    def evaluate_solvency(self, firm: 'Firm', current_tick: int) -> bool:
        """Evaluates a firm's solvency to determine bailout eligibility."""
        ...

    def issue_treasury_bonds(self, amount: int, current_tick: int) -> List[BondDTO]:
        """Issues new treasury bonds to the market."""
        ...

    def issue_treasury_bonds_synchronous(self, issuer: Any, amount_to_raise: int, current_tick: int) -> Tuple[bool, List["Transaction"]]:
        """
        Issues bonds and attempts to settle them immediately via SettlementSystem.
        Returns (success_bool, list_of_transactions).
        """
        ...

    def register_bond(self, bond: BondDTO, owner_id: AgentID) -> None:
        """
        Registers a newly issued bond in the system ledger.
        This does NOT handle money transfer, only state tracking.
        """
        ...

    def collect_corporate_tax(self, firm: IFinancialAgent, tax_amount: int) -> bool:
        """Collects corporate tax using atomic settlement."""
        ...

    def request_bailout_loan(self, firm: 'Firm', amount: int) -> Optional[GrantBailoutCommand]:
        """
        Validates and creates a command to grant a bailout loan.
        Does not execute the transfer or state update.
        """
        ...

    def service_debt(self, current_tick: int) -> List["Transaction"]:
        """Manages the servicing of outstanding government debt."""
        ...

    def process_loan_application(
        self,
        borrower_id: AgentID,
        amount: int,
        borrower_profile: BorrowerProfileDTO,
        current_tick: int
    ) -> Tuple[Optional[LoanInfoDTO], List["Transaction"]]:
        """Orchestrates the loan application process."""
        ...

    def get_customer_balance(self, bank_id: AgentID, customer_id: AgentID) -> int:
        """Query the ledger for deposit balance."""
        ...

    def get_customer_debt_status(self, bank_id: AgentID, customer_id: AgentID) -> List[LoanInfoDTO]:
        """Query the ledger for loans."""
        ...

    def close_deposit_account(self, bank_id: AgentID, agent_id: AgentID) -> int:
        """
        Closes a deposit account and returns the balance in pennies.
        Removes the deposit record from the ledger.
        """
        ...

    def record_loan_repayment(self, loan_id: str, amount: int) -> int:
        """
        Records a repayment against a specific loan.
        Reduces the principal balance. Returns the amount actually applied.
        """
        ...

    def repay_any_debt(self, borrower_id: AgentID, amount: int) -> int:
        """
        Applies a repayment amount to any outstanding debts of the borrower,
        prioritizing oldest loans. Returns total amount applied.
        """
        ...


@dataclass(frozen=True)
class OMOInstructionDTO:
    """
    Data Transfer Object for Open Market Operation instructions.
    Generated by a policy engine (e.g., in Government) and consumed by the executor.
    """
    operation_type: Literal['purchase', 'sale']
    target_amount: int
    # Optional: Could add target_price_limit, order_type etc. for more advanced ops


@runtime_checkable
class IMonetaryOperations(Protocol):
    """
    Interface for a system that executes monetary operations like OMO.
    """
    def execute_open_market_operation(self, instruction: OMOInstructionDTO) -> List["Order"]:
        """
        Takes an instruction and creates market orders to fulfill it.

        Args:
            instruction: The DTO containing the operational details.

        Returns:
            A list of Order objects to be placed on the SecurityMarket.
        """
        ...


@runtime_checkable
class ICentralBank(IMonetaryOperations, Protocol):
    """
    Represents the Central Bank entity, responsible for executing monetary policy.
    """
    id: AgentID

    def process_omo_settlement(self, transaction: "Transaction") -> None:
        """
        Callback for SettlementSystem to notify the Central Bank about
        a completed OMO transaction, allowing it to update internal state if needed.
        This is primarily for logging and verification. The actual money supply
        update happens in Government's ledger.
        """
        ...

# --- Portfolio Interfaces (TD-160) ---

# --- Interfaces for Data Access ---

@dataclass(frozen=True)
class SagaStateDTO:
    """Generic DTO for representing the state of a saga."""
    saga_id: UUID
    state: str
    payload: Dict[str, Any]
    created_at: int
    updated_at: int

class IRealEstateRegistry(ABC):
    """
    An interface for querying the state of real estate assets,
    decoupling models from business logic.
    """
    @abstractmethod
    def is_under_contract(self, property_id: int) -> bool:
        """
        Checks if a property is currently involved in an active purchase Saga.
        This is the single source of truth for the "under contract" status.
        """
        ...

    @abstractmethod
    def set_under_contract(self, property_id: int, saga_id: UUID) -> bool:
        """Locks a property, preventing other sales. Returns False if already locked."""
        ...

    @abstractmethod
    def release_contract(self, property_id: int, saga_id: UUID) -> bool:
        """Releases the lock on a property."""
        ...

    @abstractmethod
    def add_lien(self, property_id: int, loan_id: str, lienholder_id: AgentID, principal: int) -> Optional[str]:
        """Adds a lien to a property, returns a unique lien_id."""
        ...

    @abstractmethod
    def remove_lien(self, property_id: int, lien_id: str) -> bool:
        """Removes a lien from a property."""
        ...

    @abstractmethod
    def transfer_ownership(self, property_id: int, new_owner_id: AgentID) -> bool:
        """Finalizes the transfer of the property."""
        ...

class ISagaRepository(ABC):
    """
    Interface for querying the state of active Sagas.
    """
    @abstractmethod
    def find_active_saga_for_property(self, property_id: int) -> Optional[SagaStateDTO]:
        """
        Finds an active (non-completed, non-failed) housing transaction saga
        for a given property ID. Returns the saga state DTO if found, else None.
        """
        ...

@runtime_checkable
class IPortfolioHandler(Protocol):
    """
    An interface for entities that can own and transact with portfolio assets.
    This contract decouples the SettlementSystem from agent-specific implementations.
    """

    def get_portfolio(self) -> PortfolioDTO:
        """Returns a complete, structured snapshot of the agent's portfolio."""
        ...

    def receive_portfolio(self, portfolio: PortfolioDTO) -> None:
        """
        Receives and integrates a full portfolio of assets.
        This method must handle the addition of assets to the agent's holdings.
        """
        ...

    def clear_portfolio(self) -> None:
        """
        Atomically clears all portfolio assets from the agent.
        Used to transfer assets to an escrow account.
        """
        ...

@runtime_checkable
class IHeirProvider(Protocol):
    """An interface for agents that can designate an heir."""

    def get_heir(self) -> Any: # Should resolve to IPortfolioHandler & IFinancialEntity
        """Returns the designated heir, or None if there is no heir."""
        ...

@runtime_checkable
class ICreditFrozen(Protocol):
    """
    Protocol for agents that can have their credit frozen (e.g., due to bankruptcy).
    """
    @property
    def credit_frozen_until_tick(self) -> int:
        """The simulation tick until which the agent's credit is frozen."""
        ...

    @credit_frozen_until_tick.setter
    def credit_frozen_until_tick(self, value: int) -> None:
        """Sets the tick until which the agent's credit is frozen."""
        ...

class ITaxService(ABC):
    @abstractmethod
    def calculate_liquidation_tax_claims(self, firm: Firm) -> List[Claim]:
        """Calculates corporate tax claims for a firm in liquidation."""
        ...

# --- Shareholder Registry Interfaces (TD-275) ---

@dataclass(frozen=True)
class ShareholderData:
    agent_id: AgentID
    firm_id: AgentID
    quantity: float

@runtime_checkable
class IShareholderView(Protocol):
    """View interface for a firm from the perspective of the stock market."""
    id: AgentID
    is_active: bool
    def get_book_value_per_share(self) -> float: ...

@runtime_checkable
class IShareholderRegistry(Protocol):
    """Single source of truth for stock ownership."""
    def register_shares(self, firm_id: AgentID, agent_id: AgentID, quantity: float) -> None:
        """Adds/removes shares. Zero quantity removes the registry entry."""
        ...
    def get_shareholders_of_firm(self, firm_id: AgentID) -> List[ShareholderData]:
        """Returns list of owners for a firm."""
        ...
    def get_total_shares(self, firm_id: AgentID) -> float:
        """Returns total outstanding shares."""
        ...

# --- Bank Decomposition Interfaces (TD-274) ---

@runtime_checkable
class ILoanManager(Protocol):
    """Interface for managing the entire lifecycle of loans."""
    def submit_loan_application(self, application: LoanApplicationDTO) -> str: ...
    def process_applications(self) -> None: ...
    def service_loans(self, current_tick: int, payment_callback: Callable[[AgentID, int], bool]) -> List[Any]:
        """
        Calculates interest and attempts to collect payments via callback.
        Returns generated transactions or events.
        """
        ...
    def get_loan_by_id(self, loan_id: str) -> Optional[LoanDTO]: ...
    def get_loans_for_agent(self, agent_id: AgentID) -> List[LoanDTO]: ...
    def repay_loan(self, loan_id: str, amount: int) -> bool: ...

@runtime_checkable
class IDepositManager(Protocol):
    """Interface for managing agent deposit accounts."""
    def create_deposit(self, owner_id: AgentID, amount: int, interest_rate: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> str: ...
    def get_balance(self, agent_id: AgentID) -> int: ...
    def get_deposit_dto(self, agent_id: AgentID) -> Optional[DepositDTO]: ...
    def calculate_interest(self, current_tick: int) -> List[Tuple[AgentID, int]]:
        """
        Calculates interest due for all deposits.
        Returns a list of (depositor_id, interest_amount).
        """
        ...
    def withdraw(self, agent_id: AgentID, amount: int) -> bool: ...
    def get_total_deposits(self) -> int: ...

# ==============================================================================
# === ADDITIONS FOR SOLVENCY CHECK ENGINE
# ==============================================================================

# --- Data Transfer Objects (DTOs) ---

@dataclass(frozen=True)
class SolvencyCheckInputDTO:
    """Input DTO containing an entity's asset and liability totals."""
    entity_id: str
    total_assets: float
    total_liabilities: float

@dataclass(frozen=True)
class SolvencyCheckOutputDTO:
    """Output DTO reporting the results of a solvency check."""
    entity_id: str
    is_solvent: bool
    net_worth: float
    debt_to_asset_ratio: float # liabilities / assets


# --- Engine Interface ---

@runtime_checkable
class SolvencyEngine(Protocol):
    """
    A stateless engine for checking the financial solvency of an entity.
    """

    def check(self, inputs: SolvencyCheckInputDTO) -> SolvencyCheckOutputDTO:
        """
        Evaluates solvency based on assets and liabilities.

        Args:
            inputs: A DTO containing the entity's total assets and liabilities.

        Returns:
            A DTO reporting solvency status, net worth, and key ratios.
        """
        ...

@runtime_checkable
class IIncomeTracker(Protocol):
    """Protocol for entities that track their income sources."""
    def add_labor_income(self, amount: int) -> None:
        ...

@runtime_checkable
class IConsumptionTracker(Protocol):
    """Protocol for entities that track their consumption expenditure."""
    def add_consumption_expenditure(self, amount: int, item_id: Optional[str] = None) -> None:
        ...

@runtime_checkable
class IEconomicMetricsService(Protocol):
    """
    Protocol for recording economic metrics such as withdrawals for panic indexing.
    """
    def record_withdrawal(self, amount_pennies: int) -> None:
        """Records a withdrawal event."""
        ...

class IPanicRecorder(Protocol):
    """Protocol for recording panic metrics (e.g., bank run withdrawals)."""
    def record_withdrawal(self, amount_pennies: int) -> None: ...

@runtime_checkable
class ISalesTracker(Protocol):
    """Protocol for tracking sales metrics."""
    sales_volume_this_tick: float
    def record_sale(self, item_id: str, quantity: float, current_tick: int) -> None: ...

@runtime_checkable
class IRevenueTracker(Protocol):
    """Protocol for tracking revenue."""
    def record_revenue(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None: ...

@runtime_checkable
class IExpenseTracker(Protocol):
    """Protocol for tracking expenses."""
    def record_expense(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None: ...

@runtime_checkable
class IConsumer(Protocol):
    """Protocol for agents that consume goods."""
    def consume(self, item_id: str, quantity: float, current_tick: int) -> None: ...
    def record_consumption(self, quantity: float, is_food: bool = False) -> None: ...

@runtime_checkable
class ISolvencyChecker(Protocol):
    """Protocol for agents that can check their own solvency."""
    def check_solvency(self, government: Any) -> None: ...

@runtime_checkable
class ILoanRepayer(Protocol):
    """Protocol for entities that can repay loans."""
    def repay_loan(self, loan_id: str, amount: int) -> int: ...

# ==============================================================================
# === TRANSACTION HANDLER PROTOCOLS (TD-RUNTIME-TX-HANDLER)
# ==============================================================================

class TransactionType(str, Enum):
    TRANSFER = "TRANSFER"
    PAYMENT = "PAYMENT"
    TAX = "TAX"
    BAILOUT = "BAILOUT"
    BOND_ISSUANCE = "BOND_ISSUANCE"
    # Legacy/Market types
    TRADE = "TRADE"
    HOUSING = "housing"
    GOODS = "goods"
    LABOR = "labor"
    FX_SWAP = "FX_SWAP" # Phase 4.1: Barter-FX

@dataclass(frozen=True)
class BondIssuanceRequestDTO:
    """
    DTO for Bond Issuance Transaction.
    Represents the primary market sale of a bond from an Issuer to a Buyer.
    """
    issuer_id: AgentID
    buyer_id: AgentID
    face_value: int         # Face value per bond in pennies
    issue_price: int        # Actual price paid per bond in pennies
    quantity: int           # Number of bonds
    coupon_rate: float      # Annual coupon rate (0.05 = 5%)
    maturity_tick: int      # Tick when the bond matures
    bond_series_id: Optional[str] = None # Optional ID for grouping

@runtime_checkable
class ITransactionHandler(Protocol):
    """
    Protocol for specialized transaction logic.
    Each TransactionType maps to a concrete implementation of this protocol.
    """
    def validate(self, request: Any, context: Any) -> bool:
        """
        Pure validation logic. Checks solvency, permissions, and data integrity.
        Must NOT mutate state.
        """
        ...

    def execute(self, request: Any, context: Any) -> Any:
        """
        Executes the transaction.
        Responsible for calling the appropriate System/Service to mutate state.
        Returns a TransactionResultDTO-like object.
        """
        ...

    def rollback(self, transaction_id: str, context: Any) -> bool:
        """
        Reverses the transaction effects.
        Critical for Atomic Sagas.
        """
        ...

@runtime_checkable
class IBondMarketSystem(Protocol):
    """
    Interface for the Bond Market System.
    Handles the lifecycle of bond assets (creation, registration, redemption).
    """
    def issue_bond(self, request: BondIssuanceRequestDTO) -> bool:
        """
        Creates the Bond asset, assigns it to the Buyer, and registers the Liability to the Issuer.
        """
        ...

    def register_bond_series(self, issuer_id: AgentID, series_id: str, details: Dict[str, Any]) -> None:
        """
        Registers a new bond series in the security master.
        """
        ...

@runtime_checkable
class ITransactionEngine(Protocol):
    """
    Interface for the central Transaction Engine (High-Level).
    """
    def register_handler(self, tx_type: TransactionType, handler: ITransactionHandler) -> None:
        """
        Registers a handler for a specific transaction type.
        """
        ...

    def process_transaction(self, tx_type: TransactionType, data: Any) -> Any:
        """
        Dispatches the transaction to the registered handler.
        """
        ...

# ==============================================================================
# === BANK REGISTRY PROTOCOLS
# ==============================================================================

@runtime_checkable
class IBankRegistry(Protocol):
    """
    Interface for the Bank Registry service.
    Manages the collection of bank states within the financial system.
    """
    @property
    def banks_dict(self) -> Dict[AgentID, "BankStateDTO"]:
        """
        Returns the underlying dictionary of banks.
        Required for integration with FinancialLedgerDTO.
        """
        ...

    def register_bank(self, bank_state: "BankStateDTO") -> None:
        """Registers a bank state."""
        ...

    def get_bank(self, bank_id: AgentID) -> Optional["BankStateDTO"]:
        """Retrieves a bank state by ID."""
        ...

    def get_all_banks(self) -> List["BankStateDTO"]:
        """Returns all registered banks."""
        ...

    def get_deposit(self, bank_id: AgentID, deposit_id: str) -> Optional["DepositStateDTO"]:
        """Retrieves a specific deposit state."""
        ...

    def get_loan(self, bank_id: AgentID, loan_id: str) -> Optional["LoanStateDTO"]:
        """Retrieves a specific loan state."""
        ...
