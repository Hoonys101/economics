import abc
from _typeshed import Incomplete
from abc import ABC, abstractmethod
from dataclasses import dataclass, field as field
from enum import Enum
from modules.common.financial.api import IFinancialAgent as IFinancialAgent
from modules.common.financial.dtos import Claim as Claim, MoneyDTO as MoneyDTO
from modules.finance.dtos import BailoutCovenant as BailoutCovenant, BailoutLoanDTO as BailoutLoanDTO, BondDTO as BondDTO, BorrowerProfileDTO as BorrowerProfileDTO, CreditAssessmentResultDTO as CreditAssessmentResultDTO, DebtStatusDTO as DebtStatusDTO, DepositDTO as DepositDTO, EquityStake as EquityStake, FXMatchDTO as FXMatchDTO, GrantBailoutCommand as GrantBailoutCommand, LienDTO as LienDTO, LoanApplicationDTO as LoanApplicationDTO, LoanDTO as LoanDTO, MortgageApplicationDTO as MortgageApplicationDTO, MultiCurrencyWalletDTO as MultiCurrencyWalletDTO, PortfolioAsset as PortfolioAsset, PortfolioDTO as PortfolioDTO, SettlementOrder as SettlementOrder, TaxCollectionResult as TaxCollectionResult
from modules.finance.engine_api import BankStateDTO as BankStateDTO, DepositStateDTO as DepositStateDTO, LoanStateDTO as LoanStateDTO
from modules.finance.wallet.api import IWallet as IWallet
from modules.government.api import IGovernment as IGovernment
from modules.hr.api import IHRService as IHRService
from modules.simulation.api import AgentID as AgentID, AnyAgentID as AnyAgentID, EconomicIndicatorsDTO as EconomicIndicatorsDTO
from modules.system.api import CurrencyCode as CurrencyCode, DEFAULT_CURRENCY as DEFAULT_CURRENCY, MarketContextDTO as MarketContextDTO
from simulation.dtos.api import GovernmentSensoryDTO as GovernmentSensoryDTO
from simulation.models import Order as Order, Transaction as Transaction
from typing import Any, Callable, Literal, Protocol
from uuid import UUID

class IFinancialEntity(Protocol):
    """
    Standard interface for any entity capable of holding and transferring financial value.
    Enforces strict integer arithmetic for all monetary operations.
    """
    id: AgentID
    @property
    def balance_pennies(self) -> int:
        """Returns the balance in the default currency (pennies)."""
    def deposit(self, amount_pennies: int, currency: CurrencyCode = ...) -> None:
        """
        Deposits funds into the entity's wallet.
        MUST raise TypeError if amount_pennies is float.
        """
    def withdraw(self, amount_pennies: int, currency: CurrencyCode = ...) -> None:
        """
        Withdraws funds from the entity's wallet.
        MUST raise TypeError if amount_pennies is float.
        MUST raise InsufficientFundsError if balance is insufficient (unless overdraft allowed).
        """

@dataclass(frozen=True)
class SettlementVerificationDTO:
    """
    Result of a Zero-Sum integrity check after a batch settlement.
    """
    tick: int
    total_debits: int
    total_credits: int
    delta: int
    is_balanced: bool
    transaction_ids: list[str]

class FloatIncursionError(TypeError):
    """Raised when a float is passed to a strict integer financial API."""
class ZeroSumViolationError(RuntimeError):
    """Raised when a settlement operation fails to balance (Debits != Credits)."""

class ITransaction(Protocol):
    """Module A: Protocol for a completed financial transaction."""
    sender_id: AgentID
    receiver_id: AgentID
    amount_pennies: int
    tick: int
    transaction_type: str
    memo: str | None

class Firm: ...
class Household: ...

class InsufficientFundsError(Exception):
    """
    Custom exception to be raised when an operation cannot be completed due to lack of funds.
    """
    required: Incomplete
    available: Incomplete
    def __init__(self, message: str, required: MoneyDTO | None = None, available: MoneyDTO | None = None) -> None: ...

class LoanNotFoundError(Exception):
    """Raised when a specified loan is not found."""
class LoanRepaymentError(Exception):
    """Raised when there is an issue with loan repayment."""
class LoanRollbackError(Exception):
    """Raised when a loan cancellation fails to reverse the associated deposit."""

@dataclass(frozen=True)
class LiquidationContext:
    """Context object to supply necessary services for claim calculation."""
    current_tick: int
    hr_service: IHRService | None = ...
    tax_service: ITaxService | Any | None = ...
    shareholder_registry: IShareholderRegistry | None = ...

class IConfig(Protocol):
    """Protocol for configuration module."""
    def get(self, key: str, default: Any = None) -> Any: ...

class IFinancialFirm(IFinancialEntity, Protocol):
    """
    Interface for a Firm entity used in financial analysis (e.g., Solvency).
    Ensures strict typing for solvency checks and financial reporting.
    """
    id: AgentID
    @property
    def age(self) -> int:
        """The age of the firm in ticks."""
    @age.setter
    def age(self, value: int) -> None: ...
    @property
    def capital_stock_units(self) -> int:
        """The capital stock quantity in units."""
    @property
    def inventory_value_pennies(self) -> int:
        """The total value of inventory in pennies."""
    @property
    def monthly_wage_bill_pennies(self) -> int:
        """The total monthly wage bill in pennies."""
    @property
    def total_debt_pennies(self) -> int:
        """The total outstanding debt in pennies."""
    @property
    def retained_earnings_pennies(self) -> int:
        """The retained earnings in pennies."""
    @property
    def average_profit_pennies(self) -> int:
        """The average profit over the relevant history in pennies."""

class IFinanceDepartment(Protocol):
    """
    Interface for a Firm's financial operations, designed for a multi-currency environment.
    MIGRATION: All monetary values are integers (pennies).
    """
    @property
    @abstractmethod
    def balance(self) -> dict[CurrencyCode, int]:
        """Provides direct access to the raw balances dict."""
    @abstractmethod
    def get_balance(self, currency: CurrencyCode) -> int:
        """Gets the balance for a specific currency."""
    @abstractmethod
    def deposit(self, amount: int, currency: CurrencyCode):
        """Deposits a specific amount of a given currency."""
    @abstractmethod
    def withdraw(self, amount: int, currency: CurrencyCode):
        """Withdraws a specific amount of a given currency. Raises InsufficientFundsError if needed."""
    @abstractmethod
    def get_financial_snapshot(self) -> dict[str, MoneyDTO | MultiCurrencyWalletDTO | float]:
        """Returns a comprehensive, currency-aware snapshot of the firm's financials."""
    @abstractmethod
    def calculate_valuation(self, market_context: MarketContextDTO) -> MoneyDTO:
        """
        Calculates the firm's total valuation, converted to its primary currency.
        Requires current market context.
        """
    @abstractmethod
    def generate_financial_transactions(self, government: Any, all_households: list[Any], current_time: int, market_context: MarketContextDTO) -> list[Any]:
        """
        Generates all standard financial transactions (taxes, dividends, maintenance)
        in a currency-aware manner.
        """
    @abstractmethod
    def set_dividend_rate(self, new_rate: float) -> None:
        """Sets the dividend rate."""
    @abstractmethod
    def pay_ad_hoc_tax(self, amount: int, currency: CurrencyCode, reason: str, government: Any, current_time: int) -> None:
        """Pays a one-time tax of a specific currency."""

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

class ILiquidatable(Protocol):
    """
    An interface for any entity that can undergo a formal liquidation process.
    Provides all necessary financial claims and asset information to a liquidator.
    """
    id: AgentID
    def liquidate_assets(self, current_tick: int) -> dict[CurrencyCode, int]:
        """
        Performs internal write-offs of non-cash assets (inventory, capital)
        and returns a dictionary of all remaining cash-equivalent assets by currency.
        This signals the final step before cash distribution begins.
        """
    def get_all_claims(self, ctx: LiquidationContext) -> list[Claim]:
        """
        Aggregates all non-equity claims (HR, Tax, Debt) against the entity.
        The implementation is responsible for determining the amounts and creditors.
        """
    def get_equity_stakes(self, ctx: LiquidationContext) -> list[EquityStake]:
        """
        Returns a list of all shareholders and their proportional stake for Tier 5 distribution.
        An empty list signifies no equity holders.
        """

class IBankService(Protocol):
    """
    Interface for Bank Services used by Markets.
    """
    def get_interest_rate(self) -> float: ...
    def grant_loan(self, borrower_id: int, amount: int, interest_rate: float, due_tick: int | None = None, borrower_profile: BorrowerProfileDTO | None = None) -> tuple[LoanDTO, Any] | None: ...
    def stage_loan(self, borrower_id: int, amount: int, interest_rate: float, due_tick: int | None, borrower_profile: BorrowerProfileDTO | None) -> LoanDTO | None: ...
    def repay_loan(self, loan_id: str, amount: int) -> int: ...

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
    @abc.abstractmethod
    def get_debt_status(self, borrower_id: AgentID) -> DebtStatusDTO:
        """
        Retrieves the comprehensive debt status for a given borrower.
        """
    @abc.abstractmethod
    def terminate_loan(self, loan_id: str) -> Transaction | None:
        """
        Forcefully terminates a loan (e.g. foreclosure or voiding).
        """
    @abc.abstractmethod
    def withdraw_for_customer(self, agent_id: AgentID, amount: int) -> bool:
        """
        Withdraws funds from a customer's deposit account.
        """
    @abc.abstractmethod
    def get_total_deposits(self) -> int:
        """
        Returns the sum of all customer deposits held by the bank.
        """
    @abc.abstractmethod
    def close_account(self, agent_id: AgentID) -> int:
        """
        Closes the deposit account for the agent and returns the final balance.
        """
    @abc.abstractmethod
    def repay_loan(self, loan_id: str, amount: int) -> int:
        """
        Records a repayment for a specific loan. Returns the amount applied.
        This method updates the ledger but does NOT transfer funds.
        """
    @abc.abstractmethod
    def receive_repayment(self, borrower_id: AgentID, amount: int) -> int:
        """
        Receives a generic repayment from a borrower and applies it to outstanding debt.
        Returns the total amount applied.
        """

class IFiscalMonitor(Protocol):
    """Interface for the fiscal health analysis component."""
    def get_debt_to_gdp_ratio(self, government: IGovernment, indicators: EconomicIndicatorsDTO) -> float: ...

class IGovernmentFinance(IFinancialAgent, Protocol):
    """Interface for Government interaction within FinanceSystem."""
    total_debt: int
    sensory_data: GovernmentSensoryDTO | None

class IAccountRegistry(Protocol):
    """
    Module A: Interface for the Bank Account Directory Service.
    Decouples account lookup from transaction settlement.
    """
    def register_account(self, bank_id: AgentID, agent_id: AgentID) -> None:
        """Registers an account link between a bank and an agent."""
    def deregister_account(self, bank_id: AgentID, agent_id: AgentID) -> None:
        """Removes an account link between a bank and an agent."""
    def get_account_holders(self, bank_id: AgentID) -> list[AgentID]:
        """Returns a list of all agents holding accounts at the specified bank."""
    def get_agent_banks(self, agent_id: AgentID) -> list[AgentID]:
        """Returns a list of banks where the agent holds an account."""
    def remove_agent_from_all_accounts(self, agent_id: AgentID) -> None:
        """Removes an agent from all bank account indices."""

class IMonetaryLedger(Protocol):
    """
    Single Source of Truth (SSoT) for M2 Money Supply tracking.
    Records all authorized monetary expansions and contractions.
    """
    def get_total_m2_pennies(self, currency: CurrencyCode = ...) -> int:
        """Calculates total M2 = Circulating Cash + Total Deposits."""
    def get_expected_m2_pennies(self, currency: CurrencyCode = ...) -> int:
        """Returns the authorized baseline money supply including all expansions."""
    def record_monetary_expansion(self, amount_pennies: int, source: str, currency: CurrencyCode = ...) -> None:
        """Records authorized money creation (e.g., Central Bank OMO, Bank Loans)."""
    def record_monetary_contraction(self, amount_pennies: int, source: str, currency: CurrencyCode = ...) -> None:
        """Records authorized money destruction (e.g., Loan Repayments, Central Bank QT)."""
    def set_expected_m2(self, amount_pennies: int, currency: CurrencyCode = ...) -> None:
        """Sets the baseline M2 (e.g. at genesis)."""
    def get_system_debt_pennies(self, currency: CurrencyCode = ...) -> int:
        """
        Returns the total accumulated system debt.
        Resolves the O(N) aggregation bottleneck by returning a running total.
        """
    def record_system_debt_increase(self, amount_pennies: int, source: str, currency: CurrencyCode = ...) -> None:
        """
        Records an increase in system debt.
        Triggered when system agents (e.g., PublicManager, Government) utilize overdrafts or issue bonds.
        """
    def record_system_debt_decrease(self, amount_pennies: int, source: str, currency: CurrencyCode = ...) -> None:
        """
        Records a decrease in system debt.
        Triggered when system debt is repaid or reconciled.
        """
    def record_credit_expansion(self, amount: float, saga_id: UUID, loan_id: Any, reason: str) -> None: ...
    def record_credit_destruction(self, amount: float, saga_id: UUID, loan_id: Any, reason: str) -> None: ...

class ISettlementSystem(IAccountRegistry, Protocol):
    """
    The transactional kernel for all financial operations.
    Responsible for ATOMIC, ZERO-SUM transfers between entities.
    """
    def get_total_m2_pennies(self, currency: CurrencyCode = ...) -> int:
        """Calculates total M2 = Circulating Cash + Total Deposits."""
    def get_total_circulating_cash(self, currency: CurrencyCode = ...) -> int:
        """Returns total physical cash held by non-system agents (M0 outside bank reserves)."""
    def set_monetary_ledger(self, ledger: IMonetaryLedger) -> None:
        """Injects the Monetary Ledger for tracking expansions/contractions."""
    def transfer(self, debit_agent: IFinancialEntity, credit_agent: IFinancialEntity, amount: int, memo: str, debit_context: dict[str, Any] | None = None, credit_context: dict[str, Any] | None = None, tick: int = 0, currency: CurrencyCode = ...) -> ITransaction | None:
        """
        Executes an immediate, single transfer.
        MUST enforce:
        1. amount is int (no floats).
        2. debit_agent has funds (or overdraft).
        3. Zero-sum outcome (Debit - Credit == 0).
        """
    def audit_total_m2(self, expected_total: int | None = None) -> bool:
        """
        Audits the total M2 money supply in the system against registered CurrencyHolders.
        """
    def execute_swap(self, match: FXMatchDTO) -> ITransaction | None:
        """
        Phase 4.1: Executes an atomic currency swap (Barter FX).
        Ensures both legs (A->B, B->A) succeed or neither occurs.
        """
    def get_balance(self, agent_id: AgentID, currency: CurrencyCode = ...) -> int:
        """
        Queries the Single Source of Truth for an agent's current balance.
        This is the ONLY permissible way to check another agent's funds.
        """

class IMonetaryAuthority(ISettlementSystem, Protocol):
    """
    Extended interface for authorized NON-ZERO-SUM operations.
    Used by Central Bank and Government (Minting/Burning).
    """
    def mint_and_distribute(self, target_agent_id: int, amount: int, tick: int = 0, reason: str = 'god_mode_injection') -> bool:
        """
        Creates new money (M2 Expansion).
        Records creation event in MonetaryLedger.
        """
    def transfer_and_destroy(self, source: IFinancialEntity, sink_authority: IFinancialEntity, amount: int, reason: str, tick: int, currency: CurrencyCode = ...) -> Any:
        """
        Destroys money (M2 Contraction).
        Records destruction event in MonetaryLedger.
        """
    def create_and_transfer(self, source_authority: IFinancialAgent, destination: IFinancialAgent, amount: int, reason: str, tick: int, currency: CurrencyCode = ...) -> ITransaction | None:
        """Creates new money (or grants) and transfers it to an agent."""
    def record_liquidation(self, agent: IFinancialAgent, inventory_value: int, capital_value: int, recovered_cash: int, reason: str, tick: int, government_agent: IFinancialAgent | None = None) -> None:
        """
        Records the outcome of an asset liquidation.
        """

class IFinanceSystem(Protocol):
    """Interface for the sovereign debt and corporate bailout system."""
    def evaluate_solvency(self, firm: Firm, current_tick: int) -> bool:
        """Evaluates a firm's solvency to determine bailout eligibility."""
    def issue_treasury_bonds(self, amount: int, current_tick: int) -> list[BondDTO]:
        """Issues new treasury bonds to the market."""
    def issue_treasury_bonds_synchronous(self, issuer: Any, amount_to_raise: int, current_tick: int) -> tuple[bool, list['Transaction']]:
        """
        Issues bonds and attempts to settle them immediately via SettlementSystem.
        Returns (success_bool, list_of_transactions).
        """
    def register_bond(self, bond: BondDTO, owner_id: AgentID) -> None:
        """
        Registers a newly issued bond in the system ledger.
        This does NOT handle money transfer, only state tracking.
        """
    def collect_corporate_tax(self, firm: IFinancialAgent, tax_amount: int) -> bool:
        """Collects corporate tax using atomic settlement."""
    def request_bailout_loan(self, firm: Firm, amount: int) -> GrantBailoutCommand | None:
        """
        Validates and creates a command to grant a bailout loan.
        Does not execute the transfer or state update.
        """
    def service_debt(self, current_tick: int) -> list['Transaction']:
        """Manages the servicing of outstanding government debt."""
    def process_loan_application(self, borrower_id: AgentID, amount: int, borrower_profile: BorrowerProfileDTO, current_tick: int) -> tuple[LoanDTO | None, list['Transaction']]:
        """Orchestrates the loan application process."""
    def get_customer_balance(self, bank_id: AgentID, customer_id: AgentID) -> int:
        """Query the ledger for deposit balance."""
    def get_customer_debt_status(self, bank_id: AgentID, customer_id: AgentID) -> list[LoanDTO]:
        """Query the ledger for loans."""
    def close_deposit_account(self, bank_id: AgentID, agent_id: AgentID) -> int:
        """
        Closes a deposit account and returns the balance in pennies.
        Removes the deposit record from the ledger.
        """
    def record_loan_repayment(self, loan_id: str, amount: int) -> int:
        """
        Records a repayment against a specific loan.
        Reduces the principal balance. Returns the amount actually applied.
        """
    def repay_any_debt(self, borrower_id: AgentID, amount: int) -> int:
        """
        Applies a repayment amount to any outstanding debts of the borrower,
        prioritizing oldest loans. Returns total amount applied.
        """

@dataclass(frozen=True)
class OMOInstructionDTO:
    """
    Data Transfer Object for Open Market Operation instructions.
    Generated by a policy engine (e.g., in Government) and consumed by the executor.
    """
    operation_type: Literal['purchase', 'sale']
    target_amount: int

class IMonetaryOperations(Protocol):
    """
    Interface for a system that executes monetary operations like OMO.
    """
    def execute_open_market_operation(self, instruction: OMOInstructionDTO) -> list['Order']:
        """
        Takes an instruction and creates market orders to fulfill it.

        Args:
            instruction: The DTO containing the operational details.

        Returns:
            A list of Order objects to be placed on the SecurityMarket.
        """

class ICentralBank(IMonetaryOperations, Protocol):
    """
    Represents the Central Bank entity, responsible for executing monetary policy.
    """
    id: AgentID
    def process_omo_settlement(self, transaction: Transaction) -> None:
        """
        Callback for SettlementSystem to notify the Central Bank about
        a completed OMO transaction, allowing it to update internal state if needed.
        This is primarily for logging and verification. The actual money supply
        update happens in Government's ledger.
        """

@dataclass(frozen=True)
class SagaStateDTO:
    """Generic DTO for representing the state of a saga."""
    saga_id: UUID
    state: str
    payload: dict[str, Any]
    created_at: int
    updated_at: int

class IRealEstateRegistry(ABC, metaclass=abc.ABCMeta):
    """
    An interface for querying the state of real estate assets,
    decoupling models from business logic.
    """
    @abstractmethod
    def is_under_contract(self, property_id: int) -> bool:
        '''
        Checks if a property is currently involved in an active purchase Saga.
        This is the single source of truth for the "under contract" status.
        '''
    @abstractmethod
    def set_under_contract(self, property_id: int, saga_id: UUID) -> bool:
        """Locks a property, preventing other sales. Returns False if already locked."""
    @abstractmethod
    def release_contract(self, property_id: int, saga_id: UUID) -> bool:
        """Releases the lock on a property."""
    @abstractmethod
    def add_lien(self, property_id: int, loan_id: str, lienholder_id: AgentID, principal: int) -> str | None:
        """Adds a lien to a property, returns a unique lien_id."""
    @abstractmethod
    def remove_lien(self, property_id: int, lien_id: str) -> bool:
        """Removes a lien from a property."""
    @abstractmethod
    def transfer_ownership(self, property_id: int, new_owner_id: AgentID) -> bool:
        """Finalizes the transfer of the property."""

class ISagaRepository(ABC, metaclass=abc.ABCMeta):
    """
    Interface for querying the state of active Sagas.
    """
    @abstractmethod
    def find_active_saga_for_property(self, property_id: int) -> SagaStateDTO | None:
        """
        Finds an active (non-completed, non-failed) housing transaction saga
        for a given property ID. Returns the saga state DTO if found, else None.
        """

class IPortfolioHandler(Protocol):
    """
    An interface for entities that can own and transact with portfolio assets.
    This contract decouples the SettlementSystem from agent-specific implementations.
    """
    def get_portfolio(self) -> PortfolioDTO:
        """Returns a complete, structured snapshot of the agent's portfolio."""
    def receive_portfolio(self, portfolio: PortfolioDTO) -> None:
        """
        Receives and integrates a full portfolio of assets.
        This method must handle the addition of assets to the agent's holdings.
        """
    def clear_portfolio(self) -> None:
        """
        Atomically clears all portfolio assets from the agent.
        Used to transfer assets to an escrow account.
        """

class IHeirProvider(Protocol):
    """An interface for agents that can designate an heir."""
    def get_heir(self) -> Any:
        """Returns the designated heir, or None if there is no heir."""

class ICreditFrozen(Protocol):
    """
    Protocol for agents that can have their credit frozen (e.g., due to bankruptcy).
    """
    @property
    def credit_frozen_until_tick(self) -> int:
        """The simulation tick until which the agent's credit is frozen."""
    @credit_frozen_until_tick.setter
    def credit_frozen_until_tick(self, value: int) -> None:
        """Sets the tick until which the agent's credit is frozen."""

class ITaxService(ABC, metaclass=abc.ABCMeta):
    @abstractmethod
    def calculate_liquidation_tax_claims(self, firm: Firm) -> list[Claim]:
        """Calculates corporate tax claims for a firm in liquidation."""

class ILiquidator(Protocol):
    """
    Protocol for performing asset liquidations and escheatment.
    Separates the financial settlement of debt from the physical asset recovery.
    """
    def liquidate_assets(self, bankrupt_agent: IFinancialAgent, assets: Any, tick: int) -> None:
        """
        Performs escheatment or mint-to-buy operations to clear bankrupt assets
        without relying on standard market constraints.
        """

@dataclass(frozen=True)
class ShareholderData:
    agent_id: AgentID
    firm_id: AgentID
    quantity: float

class IShareholderView(Protocol):
    """View interface for a firm from the perspective of the stock market."""
    id: AgentID
    is_active: bool
    def get_book_value_per_share(self) -> float: ...

class IShareholderRegistry(Protocol):
    """Single source of truth for stock ownership."""
    def register_shares(self, firm_id: AgentID, agent_id: AgentID, quantity: float) -> None:
        """Adds/removes shares. Zero quantity removes the registry entry."""
    def get_shareholders_of_firm(self, firm_id: AgentID) -> list[ShareholderData]:
        """Returns list of owners for a firm."""
    def get_total_shares(self, firm_id: AgentID) -> float:
        """Returns total outstanding shares."""

class ILoanManager(Protocol):
    """Interface for managing the entire lifecycle of loans."""
    def submit_loan_application(self, application: LoanApplicationDTO) -> str: ...
    def process_applications(self) -> None: ...
    def service_loans(self, current_tick: int, payment_callback: Callable[[AgentID, int], bool]) -> list[Any]:
        """
        Calculates interest and attempts to collect payments via callback.
        Returns generated transactions or events.
        """
    def get_loan_by_id(self, loan_id: str) -> LoanDTO | None: ...
    def get_loans_for_agent(self, agent_id: AgentID) -> list[LoanDTO]: ...
    def repay_loan(self, loan_id: str, amount: int) -> bool: ...

class IDepositManager(Protocol):
    """Interface for managing agent deposit accounts."""
    def create_deposit(self, owner_id: AgentID, amount: int, interest_rate: float, currency: CurrencyCode = ...) -> str: ...
    def get_balance(self, agent_id: AgentID) -> int: ...
    def get_deposit_dto(self, agent_id: AgentID) -> DepositDTO | None: ...
    def calculate_interest(self, current_tick: int) -> list[tuple[AgentID, int]]:
        """
        Calculates interest due for all deposits.
        Returns a list of (depositor_id, interest_amount).
        """
    def withdraw(self, agent_id: AgentID, amount: int) -> bool: ...
    def get_total_deposits(self) -> int: ...

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
    debt_to_asset_ratio: float

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

class IIncomeTracker(Protocol):
    """Protocol for entities that track their income sources."""
    def add_labor_income(self, amount: int) -> None: ...

class IConsumptionTracker(Protocol):
    """Protocol for entities that track their consumption expenditure."""
    def add_consumption_expenditure(self, amount: int, item_id: str | None = None) -> None: ...

class IEconomicMetricsService(Protocol):
    """
    Protocol for recording economic metrics such as withdrawals for panic indexing.
    """
    def record_withdrawal(self, amount_pennies: int) -> None:
        """Records a withdrawal event."""

class IPanicRecorder(Protocol):
    """Protocol for recording panic metrics (e.g., bank run withdrawals)."""
    def record_withdrawal(self, amount_pennies: int) -> None: ...

class ISalesTracker(Protocol):
    """Protocol for tracking sales metrics."""
    sales_volume_this_tick: float
    def record_sale(self, item_id: str, quantity: float, current_tick: int) -> None: ...

class IRevenueTracker(Protocol):
    """Protocol for tracking revenue."""
    def record_revenue(self, amount: int, currency: CurrencyCode = ...) -> None: ...

class IExpenseTracker(Protocol):
    """Protocol for tracking expenses."""
    def record_expense(self, amount: int, currency: CurrencyCode = ...) -> None: ...

class IConsumer(Protocol):
    """Protocol for agents that consume goods."""
    def consume(self, item_id: str, quantity: float, current_tick: int) -> None: ...
    def record_consumption(self, quantity: float, is_food: bool = False) -> None: ...

class ISolvencyChecker(Protocol):
    """Protocol for agents that can check their own solvency."""
    def check_solvency(self, government: Any) -> None: ...

class ILoanRepayer(Protocol):
    """Protocol for entities that can repay loans."""
    def repay_loan(self, loan_id: str, amount: int) -> int: ...

class TransactionType(str, Enum):
    TRANSFER = 'TRANSFER'
    PAYMENT = 'PAYMENT'
    TAX = 'TAX'
    BAILOUT = 'BAILOUT'
    BOND_ISSUANCE = 'BOND_ISSUANCE'
    TRADE = 'TRADE'
    HOUSING = 'housing'
    GOODS = 'goods'
    LABOR = 'labor'
    FX_SWAP = 'FX_SWAP'

@dataclass(frozen=True)
class BondIssuanceRequestDTO:
    """
    DTO for Bond Issuance Transaction.
    Represents the primary market sale of a bond from an Issuer to a Buyer.
    """
    issuer_id: AgentID
    buyer_id: AgentID
    face_value: int
    issue_price: int
    quantity: int
    coupon_rate: float
    maturity_tick: int
    bond_series_id: str | None = ...

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
    def execute(self, request: Any, context: Any) -> Any:
        """
        Executes the transaction.
        Responsible for calling the appropriate System/Service to mutate state.
        Returns a TransactionResultDTO-like object.
        """
    def rollback(self, transaction_id: str, context: Any) -> bool:
        """
        Reverses the transaction effects.
        Critical for Atomic Sagas.
        """

class IBondMarketSystem(Protocol):
    """
    Interface for the Bond Market System.
    Handles the lifecycle of bond assets (creation, registration, redemption).
    """
    def issue_bond(self, request: BondIssuanceRequestDTO) -> bool:
        """
        Creates the Bond asset, assigns it to the Buyer, and registers the Liability to the Issuer.
        """
    def register_bond_series(self, issuer_id: AgentID, series_id: str, details: dict[str, Any]) -> None:
        """
        Registers a new bond series in the security master.
        """

class ITransactionEngine(Protocol):
    """
    Interface for the central Transaction Engine (High-Level).
    """
    def register_handler(self, tx_type: TransactionType, handler: ITransactionHandler) -> None:
        """
        Registers a handler for a specific transaction type.
        """
    def process_transaction(self, tx_type: TransactionType, data: Any) -> Any:
        """
        Dispatches the transaction to the registered handler.
        """

class IBankRegistry(Protocol):
    """
    Interface for the Bank Registry service.
    Manages the collection of bank states within the financial system.
    """
    @property
    def banks_dict(self) -> dict[AgentID, 'BankStateDTO']:
        """
        Returns the underlying dictionary of banks.
        Required for integration with FinancialLedgerDTO.
        """
    def register_bank(self, bank_state: BankStateDTO) -> None:
        """Registers a bank state."""
    def get_bank(self, bank_id: AgentID) -> BankStateDTO | None:
        """Retrieves a bank state by ID."""
    def get_all_banks(self) -> list['BankStateDTO']:
        """Returns all registered banks."""
    def get_deposit(self, bank_id: AgentID, deposit_id: str) -> DepositStateDTO | None:
        """Retrieves a specific deposit state."""
    def get_loan(self, bank_id: AgentID, loan_id: str) -> LoanStateDTO | None:
        """Retrieves a specific loan state."""
