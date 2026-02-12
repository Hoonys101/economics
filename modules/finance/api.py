from __future__ import annotations
from typing import Protocol, Dict, List, Any, Optional, TypedDict, Literal, Tuple, runtime_checkable, TYPE_CHECKING, Union, Callable
from dataclasses import dataclass
import abc
from abc import ABC, abstractmethod
from uuid import UUID
from modules.finance.dtos import MoneyDTO, MultiCurrencyWalletDTO, LoanApplicationDTO, LoanDTO, DepositDTO
from modules.system.api import MarketContextDTO, DEFAULT_CURRENCY, CurrencyCode
from modules.simulation.api import AgentID, AnyAgentID

if TYPE_CHECKING:
    from modules.simulation.api import IGovernment, EconomicIndicatorsDTO
    from simulation.models import Order, Transaction
    from modules.common.dtos import Claim
    from modules.finance.wallet.api import IWallet
    from modules.hr.api import IHRService

# Forward reference for type hinting
class Firm: pass
class Household: pass # Assuming Household agent also interacts with the bank

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

@dataclass
class BailoutCovenant:
    """Defines the restrictive conditions attached to a bailout loan."""
    dividends_allowed: bool
    executive_salary_freeze: bool
    mandatory_repayment: float # Ratio of profit to be repaid

@dataclass
class BailoutLoanDTO:
    """Data Transfer Object for corporate bailout loans."""
    firm_id: AgentID
    amount: int
    interest_rate: float
    covenants: BailoutCovenant

@dataclass
class GrantBailoutCommand:
    """
    Command to grant a bailout loan.
    Encapsulates all necessary parameters for execution by the PolicyExecutionEngine.
    """
    firm_id: AgentID
    amount: int
    interest_rate: float
    covenants: BailoutCovenant

class SettlementOrder(TypedDict):
    """A command to execute a monetary transfer via the SettlementSystem."""
    sender_id: AgentID
    receiver_id: AgentID
    amount_pennies: int
    currency: CurrencyCode
    memo: str
    transaction_type: str # e.g., 'WAGE', 'TAX', 'PURCHASE', 'ASSET_ENDOWMENT'

# --- Portfolio DTOs (TD-160) ---

@dataclass
class PortfolioAsset:
    """Represents a single type of asset holding."""
    asset_type: str  # e.g., 'stock', 'bond'
    asset_id: str    # e.g., 'FIRM_1', 'GOV_BOND_10Y'
    quantity: float

@dataclass
class PortfolioDTO:
    """A comprehensive, serializable representation of an agent's portfolio."""
    assets: List[PortfolioAsset]

class TaxCollectionResult(TypedDict):
    """
    Represents the verified outcome of a tax collection attempt.
    """
    success: bool
    amount_collected: int
    tax_type: str
    payer_id: AgentID
    payee_id: AgentID
    error_message: Optional[str]

class LoanInfoDTO(TypedDict):
    """
    Data Transfer Object for individual loan information.
    """
    loan_id: str
    borrower_id: AgentID
    original_amount: int
    outstanding_balance: int
    interest_rate: float
    origination_tick: int
    due_tick: Optional[int]

class DebtStatusDTO(TypedDict):
    """
    Comprehensive data transfer object for a borrower's overall debt status.
    """
    borrower_id: AgentID
    total_outstanding_debt: int
    loans: List[LoanInfoDTO]
    is_insolvent: bool
    next_payment_due: Optional[int]
    next_payment_due_tick: Optional[int]

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

class BorrowerProfileDTO(TypedDict):
    """
    Data Transfer Object holding all financial data for a borrower
    needed for credit assessment. Anonymized from the concrete agent.
    """
    borrower_id: AgentID
    gross_income: int
    existing_debt_payments: int
    collateral_value: int # Value of the asset being purchased, if any
    existing_assets: int

class CreditAssessmentResultDTO(TypedDict):
    """
    The result of a credit check from the CreditScoringService.
    """
    is_approved: bool
    max_loan_amount: int
    reason: Optional[str] # Reason for denial

# --- Lien and Encumbrance DTOs ---

class LienDTO(TypedDict):
    """
    Represents a financial claim (lien) against a real estate property.
    This is the canonical data structure for all property-secured debt.
    """
    loan_id: str
    lienholder_id: AgentID  # The ID of the agent/entity holding the lien (e.g., the bank)
    principal_remaining: int
    lien_type: Literal["MORTGAGE", "TAX_LIEN", "JUDGEMENT_LIEN"]

class MortgageApplicationDTO(TypedDict):
    """
    Represents a formal mortgage application sent to the LoanMarket.
    This is the primary instrument for the new credit pipeline.
    [TD-206] Synced with MortgageApplicationRequestDTO for precision.
    """
    applicant_id: AgentID
    requested_principal: int
    purpose: Literal["MORTGAGE"]
    property_id: int
    property_value: int # Market value for LTV calculation
    applicant_monthly_income: int # For DTI calculation
    existing_monthly_debt_payments: int # For DTI calculation
    loan_term: int # Added to support calculation (implied in logic)

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

class EquityStake(TypedDict):
    """Represents a shareholder's stake for Tier 5 distribution."""
    shareholder_id: AgentID
    ratio: float # Proportional ownership, e.g., 0.1 for 10%

@dataclass
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
    Strict protocol for any agent participating in the financial system.
    Supports multi-currency operations and replaces direct attribute access.
    """
    id: AgentID

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


class IBank(IFinancialAgent, Protocol):
    """
    Interface for commercial and central banks, providing core banking services.
    Designed to be used as a dependency for Household and Firm agents.
    Inherits IFinancialAgent for its own equity/reserves management.
    """

    @abc.abstractmethod
    def grant_loan(self, borrower_id: AgentID, amount: int, interest_rate: float, due_tick: Optional[int] = None, borrower_profile: Optional[BorrowerProfileDTO] = None) -> Optional[LoanInfoDTO]:
        """
        Grants a loan to a borrower.
        """
        ...

    @abc.abstractmethod
    def stage_loan(self, borrower_id: AgentID, amount: int, interest_rate: float, due_tick: Optional[int] = None, borrower_profile: Optional[BorrowerProfileDTO] = None) -> Optional[LoanInfoDTO]:
        """
        Creates a loan record but does not disburse funds (no deposit creation).
        """
        ...

    @abc.abstractmethod
    def repay_loan(self, loan_id: str, amount: int) -> bool:
        """
        Repays a portion or the full amount of a specific loan.
        """
        ...

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

# Alias for backward compatibility during refactor
IBankService = IBank

class IFiscalMonitor(Protocol):
    """Interface for the fiscal health analysis component."""
    def get_debt_to_gdp_ratio(self, government: "IGovernment", indicators: "EconomicIndicatorsDTO") -> float: ...

class ISettlementSystem(Protocol):
    """
    Interface for the centralized settlement system.
    """

    def transfer(self, sender: IFinancialAgent, receiver: IFinancialAgent, amount_pennies: int, memo: str, currency: CurrencyCode = DEFAULT_CURRENCY) -> Optional[ITransaction]:
        """Executes an immediate, single transfer. Returns transaction or None."""
        ...

    def get_balance(self, agent_id: AgentID, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        """
        Queries the Single Source of Truth for an agent's current balance.
        This is the ONLY permissible way to check another agent's funds.
        """
        ...

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
        borrower_profile: Dict,
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


class OMOInstructionDTO(TypedDict):
    """
    Data Transfer Object for Open Market Operation instructions.
    Generated by a policy engine (e.g., in Government) and consumed by the executor.
    """
    operation_type: Literal['purchase', 'sale']
    target_amount: int
    # Optional: Could add target_price_limit, order_type etc. for more advanced ops


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
    def find_active_saga_for_property(self, property_id: int) -> Optional[dict]:
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

class ShareholderData(TypedDict):
    agent_id: AgentID
    firm_id: AgentID
    quantity: float

@runtime_checkable
class IShareholderView(Protocol):
    """View interface for a firm from the perspective of the stock market."""
    id: AgentID
    is_active: bool
    def get_book_value_per_share(self) -> float: ...

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
