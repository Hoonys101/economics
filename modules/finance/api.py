from typing import Protocol, Dict, List, Any, Optional, TypedDict, Literal, Tuple
from dataclasses import dataclass
import abc

from simulation.models import Order, Transaction

# Forward reference for type hinting
class Firm: pass
class Household: pass # Assuming Household agent also interacts with the bank

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
    """Raised when a withdrawal is attempted with insufficient funds."""
    pass

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

class IFinancialEntity(Protocol):
    """Protocol for any entity that can hold and transfer funds."""

    @property
    def id(self) -> int: ...

    @property
    def assets(self) -> float: ...

    def deposit(self, amount: float) -> None:
        """Deposits a given amount into the entity's account."""
        ...

    def withdraw(self, amount: float) -> None:
        """
        Withdraws a given amount from the entity's account.

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

class IFiscalMonitor(Protocol):
    """Interface for the fiscal health analysis component."""
    def get_debt_to_gdp_ratio(self, government_dto: Any, world_dto: Any) -> float: ...

class IFinanceSystem(Protocol):
    """Interface for the sovereign debt and corporate bailout system."""

    def evaluate_solvency(self, firm: 'Firm', current_tick: int) -> bool:
        """Evaluates a firm's solvency to determine bailout eligibility."""
        ...

    def issue_treasury_bonds(self, amount: float, current_tick: int) -> List[BondDTO]:
        """Issues new treasury bonds to the market."""
        ...

    def issue_treasury_bonds_synchronous(self, issuer: Any, amount_to_raise: float, current_tick: int) -> Tuple[bool, List[Transaction]]:
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
    def execute_open_market_operation(self, instruction: OMOInstructionDTO) -> List[Order]:
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

    def process_omo_settlement(self, transaction: Transaction) -> None:
        """
        Callback for SettlementSystem to notify the Central Bank about
        a completed OMO transaction, allowing it to update internal state if needed.
        This is primarily for logging and verification. The actual money supply
        update happens in Government's ledger.
        """
        ...
