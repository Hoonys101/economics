from __future__ import annotations
from typing import Protocol, Dict, List, Any, Optional, TypedDict, Literal, Tuple, runtime_checkable, TYPE_CHECKING, Union, Callable
from dataclasses import dataclass
import abc
from abc import ABC, abstractmethod
from uuid import UUID
from modules.finance.dtos import MoneyDTO, MultiCurrencyWalletDTO, LoanApplicationDTO, LoanDTO, DepositDTO
from modules.system.api import MarketContextDTO

if TYPE_CHECKING:
    from modules.simulation.api import IGovernment, EconomicIndicatorsDTO
    from simulation.models import Order, Transaction
    from modules.common.dtos import Claim
    from modules.finance.wallet.api import IWallet
    from modules.system.api import CurrencyCode

# Forward reference for type hinting
class Firm: pass
class Household: pass # Assuming Household agent also interacts with the bank

class IFinanceDepartment(Protocol):
    """
    Interface for a Firm's financial operations, designed for a multi-currency environment.
    """

    @property
    @abstractmethod
    def balance(self) -> Dict[CurrencyCode, float]:
        """Provides direct access to the raw balances dict."""
        ...

    @abstractmethod
    def get_balance(self, currency: CurrencyCode) -> float:
        """Gets the balance for a specific currency."""
        ...

    @abstractmethod
    def deposit(self, amount: float, currency: CurrencyCode):
        """Deposits a specific amount of a given currency."""
        ...

    @abstractmethod
    def withdraw(self, amount: float, currency: CurrencyCode):
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
    def pay_ad_hoc_tax(self, amount: float, currency: CurrencyCode, reason: str, government: Any, current_time: int) -> None:
        """Pays a one-time tax of a specific currency."""
        ...

@dataclass
class BondDTO:
    """Data Transfer Object for government bonds."""
    id: str
    issuer: str
    face_value: float
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
    firm_id: int
    amount: float
    interest_rate: float
    covenants: BailoutCovenant

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
    amount_collected: float
    tax_type: str
    payer_id: Any
    payee_id: Any
    error_message: Optional[str]

class LoanInfoDTO(TypedDict):
    """
    Data Transfer Object for individual loan information.
    """
    loan_id: str
    borrower_id: str
    original_amount: float
    outstanding_balance: float
    interest_rate: float
    origination_tick: int
    due_tick: Optional[int]

class DebtStatusDTO(TypedDict):
    """
    Comprehensive data transfer object for a borrower's overall debt status.
    """
    borrower_id: str
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
             msg = f"{message} Required: {required['amount']:.2f} {required['currency']}, Available: {available['amount']:.2f} {available['currency']}"
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
    borrower_id: str
    gross_income: float
    existing_debt_payments: float
    collateral_value: float # Value of the asset being purchased, if any
    existing_assets: float

class CreditAssessmentResultDTO(TypedDict):
    """
    The result of a credit check from the CreditScoringService.
    """
    is_approved: bool
    max_loan_amount: float
    reason: Optional[str] # Reason for denial

# --- Lien and Encumbrance DTOs ---

class LienDTO(TypedDict):
    """
    Represents a financial claim (lien) against a real estate property.
    This is the canonical data structure for all property-secured debt.
    """
    loan_id: str
    lienholder_id: int  # The ID of the agent/entity holding the lien (e.g., the bank)
    principal_remaining: float
    lien_type: Literal["MORTGAGE", "TAX_LIEN", "JUDGEMENT_LIEN"]

class MortgageApplicationDTO(TypedDict):
    """
    Represents a formal mortgage application sent to the LoanMarket.
    This is the primary instrument for the new credit pipeline.
    [TD-206] Synced with MortgageApplicationRequestDTO for precision.
    """
    applicant_id: int
    requested_principal: float
    purpose: Literal["MORTGAGE"]
    property_id: int
    property_value: float # Market value for LTV calculation
    applicant_monthly_income: float # For DTI calculation
    existing_monthly_debt_payments: float # For DTI calculation
    loan_term: int # Added to support calculation (implied in logic)

class ICreditScoringService(Protocol):
    """
    Interface for a service that assesses the creditworthiness of a potential borrower.
    """

    @abc.abstractmethod
    def assess_creditworthiness(self, profile: BorrowerProfileDTO, requested_loan_amount: float) -> CreditAssessmentResultDTO:
        """
        Evaluates a borrower's financial profile against lending criteria.

        Args:
            profile: A DTO containing the borrower's financial information.
            requested_loan_amount: The amount of the loan being requested.

        Returns:
            A DTO indicating approval status and other relevant details.
        """
        ...

@runtime_checkable
class IFinancialEntity(Protocol):
    """
    Protocol for any entity that possesses assets and participates in financial transactions.
    Native implementation operates exclusively on DEFAULT_CURRENCY.
    """
    id: int

    @property
    def assets(self) -> float:
        """Current assets in DEFAULT_CURRENCY (Read-Only)."""
        ...

    def deposit(self, amount: float) -> None:
        """Deposits a given amount of DEFAULT_CURRENCY into the entity's account."""
        ...

    def withdraw(self, amount: float) -> None:
        """
        Withdraws a given amount of DEFAULT_CURRENCY from the entity's account.

        Raises:
            InsufficientFundsError: If the withdrawal amount exceeds available funds.
        """
        ...

class IBankService(IFinancialEntity, Protocol):
    """
    Interface for commercial and central banks, providing core banking services.
    Designed to be used as a dependency for Household and Firm agents.
    """

    @abc.abstractmethod
    def grant_loan(self, borrower_id: str, amount: float, interest_rate: float, due_tick: Optional[int] = None, borrower_profile: Optional[BorrowerProfileDTO] = None) -> Optional[LoanInfoDTO]:
        """
        Grants a loan to a borrower.

        Args:
            borrower_id: The ID of the entity receiving the loan (Household or Firm).
            amount: The principal amount of the loan.
            interest_rate: The annual interest rate for the loan.
            due_tick: Optional. The simulation tick when the loan is due. If None, it's an open-ended loan.
            borrower_profile: Optional. DTO with financial data for credit scoring.

        Returns:
            A LoanInfoDTO if the loan is successfully granted, otherwise None.
        """
        ...

    @abc.abstractmethod
    def stage_loan(self, borrower_id: str, amount: float, interest_rate: float, due_tick: Optional[int] = None, borrower_profile: Optional[BorrowerProfileDTO] = None) -> Optional[LoanInfoDTO]:
        """
        Creates a loan record but does not disburse funds (no deposit creation).
        Used for atomic settlements where funds are transferred directly from Bank Reserves via SettlementSystem.

        Args:
            borrower_id: The ID of the entity receiving the loan.
            amount: The principal amount.
            interest_rate: The annual interest rate.
            due_tick: Optional due tick.
            borrower_profile: Optional credit scoring profile.

        Returns:
            A LoanInfoDTO if the loan is successfully staged, otherwise None.
        """
        ...

    @abc.abstractmethod
    def repay_loan(self, loan_id: str, amount: float) -> bool:
        """
        Repays a portion or the full amount of a specific loan.

        Args:
            loan_id: The unique identifier of the loan to be repaid.
            amount: The amount to repay.

        Returns:
            True if the repayment is successful and the loan is updated, False otherwise.

        Raises:
            LoanNotFoundError: If the loan_id does not correspond to an active loan.
            LoanRepaymentError: If there's an issue processing the repayment (e.g., negative amount).
        """
        ...

    @abc.abstractmethod
    def get_balance(self, account_id: str) -> float:
        """
        Retrieves the current balance for a given account.

        Args:
            account_id: The ID of the account owner (Household or Firm).

        Returns:
            The current monetary balance of the account.
        """
        ...

    @abc.abstractmethod
    def get_debt_status(self, borrower_id: str) -> DebtStatusDTO:
        """
        Retrieves the comprehensive debt status for a given borrower.

        Args:
            borrower_id: The ID of the entity whose debt status is requested.

        Returns:
            A DebtStatusDTO containing details about all outstanding loans and overall debt.
        """
        ...

    @abc.abstractmethod
    def terminate_loan(self, loan_id: str) -> Optional["Transaction"]:
        """
        Forcefully terminates a loan (e.g. foreclosure or voiding).
        Returns a credit_destruction transaction if balance was > 0.
        """
        ...

class IFiscalMonitor(Protocol):
    """Interface for the fiscal health analysis component."""
    def get_debt_to_gdp_ratio(self, government: "IGovernment", indicators: "EconomicIndicatorsDTO") -> float: ...

class IFinanceSystem(Protocol):
    """Interface for the sovereign debt and corporate bailout system."""

    def evaluate_solvency(self, firm: 'Firm', current_tick: int) -> bool:
        """Evaluates a firm's solvency to determine bailout eligibility."""
        ...

    def issue_treasury_bonds(self, amount: float, current_tick: int) -> List[BondDTO]:
        """Issues new treasury bonds to the market."""
        ...

    def issue_treasury_bonds_synchronous(self, issuer: Any, amount_to_raise: float, current_tick: int) -> Tuple[bool, List["Transaction"]]:
        """
        Issues bonds and attempts to settle them immediately via SettlementSystem.
        Returns (success_bool, list_of_transactions).
        """
        ...

    def collect_corporate_tax(self, firm: IFinancialEntity, tax_amount: float) -> bool:
        """Collects corporate tax using atomic settlement."""
        ...

    def grant_bailout_loan(self, firm: 'Firm', amount: float) -> Optional[BailoutLoanDTO]:
        """Converts a bailout from a grant to an interest-bearing senior loan."""
        ...

    def service_debt(self, current_tick: int) -> None:
        """Manages the servicing of outstanding government debt."""
        ...


class OMOInstructionDTO(TypedDict):
    """
    Data Transfer Object for Open Market Operation instructions.
    Generated by a policy engine (e.g., in Government) and consumed by the executor.
    """
    operation_type: Literal['purchase', 'sale']
    target_amount: float
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
    id: int

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
    def add_lien(self, property_id: int, loan_id: str, lienholder_id: int, principal: float) -> Optional[str]:
        """Adds a lien to a property, returns a unique lien_id."""
        ...

    @abstractmethod
    def remove_lien(self, property_id: int, lien_id: str) -> bool:
        """Removes a lien from a property."""
        ...

    @abstractmethod
    def transfer_ownership(self, property_id: int, new_owner_id: int) -> bool:
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
    agent_id: int
    firm_id: int
    quantity: float

class IShareholderRegistry(Protocol):
    """Single source of truth for stock ownership."""
    def register_shares(self, firm_id: int, agent_id: int, quantity: float) -> None:
        """Adds/removes shares. Zero quantity removes the registry entry."""
        ...
    def get_shareholders_of_firm(self, firm_id: int) -> List[ShareholderData]:
        """Returns list of owners for a firm."""
        ...
    def get_total_shares(self, firm_id: int) -> float:
        """Returns total outstanding shares."""
        ...

# --- Bank Decomposition Interfaces (TD-274) ---

class ILoanManager(Protocol):
    """Interface for managing the entire lifecycle of loans."""
    def submit_loan_application(self, application: LoanApplicationDTO) -> str: ...
    def process_applications(self) -> None: ...
    def service_loans(self, current_tick: int, payment_callback: Callable[[int, float], bool]) -> List[Any]:
        """
        Calculates interest and attempts to collect payments via callback.
        Returns generated transactions or events.
        """
        ...
    def get_loan_by_id(self, loan_id: str) -> Optional[LoanDTO]: ...
    def get_loans_for_agent(self, agent_id: int) -> List[LoanDTO]: ...
    def repay_loan(self, loan_id: str, amount: float) -> bool: ...

class IDepositManager(Protocol):
    """Interface for managing agent deposit accounts."""
    def create_deposit(self, owner_id: int, amount: float, interest_rate: float, currency: str = "USD") -> str: ...
    def get_balance(self, agent_id: int) -> float: ...
    def get_deposit_dto(self, agent_id: int) -> Optional[DepositDTO]: ...
    def calculate_interest(self, current_tick: int) -> List[Tuple[int, float]]:
        """
        Calculates interest due for all deposits.
        Returns a list of (depositor_id, interest_amount).
        """
        ...
    def withdraw(self, agent_id: int, amount: float) -> bool: ...
    def get_total_deposits(self) -> float: ...
