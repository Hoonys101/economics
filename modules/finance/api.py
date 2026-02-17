from __future__ import annotations
from typing import Protocol, Dict, List, Any, Optional, TypedDict, Literal, Tuple, runtime_checkable, TYPE_CHECKING, Union, Callable
from dataclasses import dataclass, field
import abc
from abc import ABC, abstractmethod
from uuid import UUID
from modules.finance.dtos import MoneyDTO, MultiCurrencyWalletDTO, LoanApplicationDTO, LoanDTO, DepositDTO
from modules.system.api import MarketContextDTO, DEFAULT_CURRENCY, CurrencyCode
from modules.simulation.api import AgentID, AnyAgentID

if TYPE_CHECKING:
    from modules.simulation.api import IGovernment, EconomicIndicatorsDTO
    from simulation.dtos.api import GovernmentSensoryDTO
    from simulation.models import Order, Transaction
    from modules.common.dtos import Claim
    from modules.finance.wallet.api import IWallet
    from modules.hr.api import IHRService

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
    def capital_stock_pennies(self) -> int:
        """The capital stock value in pennies."""
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

@dataclass
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

@dataclass
class DebtStatusDTO:
    borrower_id: int
    total_outstanding_debt: float
    loans: List[LoanInfoDTO]
    is_insolvent: bool
    next_payment_due: Optional[float]
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

@dataclass
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

class IBankService(Protocol):
    """
    Interface for Bank Services used by Markets.
    """
    def get_interest_rate(self) -> float: ...

    def grant_loan(self, borrower_id: int, amount: float, interest_rate: float, due_tick: int) -> Optional[Tuple[LoanInfoDTO, Any]]: ...

    def stage_loan(self, borrower_id: int, amount: float, interest_rate: float, due_tick: Optional[int], borrower_profile: Optional[BorrowerProfileDTO]) -> Optional[LoanInfoDTO]: ...

    def repay_loan(self, loan_id: str, amount: float) -> bool: ...

@runtime_checkable
class IBank(IBankService, IFinancialAgent, Protocol):
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

# IBankService = IBank # Removed alias

class IFiscalMonitor(Protocol):
    """Interface for the fiscal health analysis component."""
    def get_debt_to_gdp_ratio(self, government: "IGovernment", indicators: "EconomicIndicatorsDTO") -> float: ...

@runtime_checkable
class IGovernmentFinance(IFinancialAgent, Protocol):
    """Interface for Government interaction within FinanceSystem."""
    total_debt: int
    sensory_data: Optional[GovernmentSensoryDTO]

@runtime_checkable
class ISettlementSystem(Protocol):
    """
    Interface for the centralized settlement system.
    Basic financial operations for Households and Firms.
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

    def get_balance(self, agent_id: AgentID, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        """
        Queries the Single Source of Truth for an agent's current balance.
        This is the ONLY permissible way to check another agent's funds.
        """
        ...

    def get_account_holders(self, bank_id: int) -> List[int]:
        """Returns a list of all agents holding accounts at the specified bank."""
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

    def register_account(self, bank_id: int, agent_id: int) -> None:
        """
        Registers an account link between a bank and an agent.
        Used to maintain the reverse index for bank runs.
        """
        ...

    def deregister_account(self, bank_id: int, agent_id: int) -> None:
        """
        Removes an account link between a bank and an agent.
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

# ==============================================================================
# === ADDITIONS FOR SOLVENCY CHECK ENGINE
# ==============================================================================

# --- Data Transfer Objects (DTOs) ---

class SolvencyCheckInputDTO(TypedDict):
    """Input DTO containing an entity's asset and liability totals."""
    entity_id: str
    total_assets: float
    total_liabilities: float

class SolvencyCheckOutputDTO(TypedDict):
    """Output DTO reporting the results of a solvency check."""
    entity_id: str
    is_solvent: bool
    net_worth: float
    debt_to_asset_ratio: float # liabilities / assets


# --- Engine Interface ---

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
