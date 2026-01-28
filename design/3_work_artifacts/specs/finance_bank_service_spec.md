# [Refactor Request] modules/finance/api.py - IBankService

## 1. Problem Statement
The existing `IBankService` interface in `modules/finance/api.py` is incomplete and does not fully define the necessary banking operations for Household and Firm agents. This leads to tight coupling with concrete `Bank` implementations and hinders clear API contracts.

## 2. Objective
To formally define the `IBankService` interface to support deposit/withdraw, grant_loan/repay_loan, and get_balance/get_debt_status operations. This will ensure proper decoupling of agents from the `Bank` implementation and establish clear type-hinted contracts.

## 3. Target Metrics
- Clear, type-hinted methods in `IBankService`.
- Use of DTOs for complex data structures (loans, debt status).
- Adherence to `abc.ABC` for abstract methods.

## 4. Implementation Plan
### Track A: Define DTOs in `modules/finance/api.py`
- Create `LoanInfoDTO` (TypedDict) for individual loan details.
- Create `DebtStatusDTO` (TypedDict) for comprehensive borrower debt status.
- Add `LoanNotFoundError` and `LoanRepaymentError` custom exceptions.

### Track B: Update `IBankService` in `modules/finance/api.py`
- Ensure `IBankService` inherits from `IFinancialEntity` (which provides deposit/withdraw).
- Add `grant_loan` method with `borrower_id`, `amount`, `interest_rate`, `due_tick` parameters, returning `Optional[LoanInfoDTO]`.
- Add `repay_loan` method with `loan_id`, `amount` parameters, returning `bool`, and raising `LoanNotFoundError`, `LoanRepaymentError`.
- Add `get_balance` method with `account_id` parameter, returning `float`.
- Add `get_debt_status` method with `borrower_id` parameter, returning `DebtStatusDTO`.

## 5. Verification
- **Code Review**: Ensure `modules/finance/api.py` matches the provided content in this spec (especially the DTOs and `IBankService` methods).
- **Static Analysis**: Run `mypy modules/finance/api.py` to ensure all type hints are correct and consistent.
- **Unit Tests**:
    - New tests will be created in `tests/finance/test_bank_service_interface.py` to verify that a mock implementation of `IBankService` can correctly satisfy the interface and that all methods have the correct signatures.

## 6. Jules Assignment
| Track | Task | 파일 |
|---|---|---|
| A, B | Implement DTOs and `IBankService` in `modules/finance/api.py` | `modules/finance/api.py` |

---

## API Definition for `modules/finance/api.py` (Intended Content)

```python
from typing import Protocol, Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass
import abc

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
    def grant_loan(self, borrower_id: str, amount: float, interest_rate: float, due_tick: Optional[int] = None) -> Optional[LoanInfoDTO]:
        """
        Grants a loan to a borrower.

        Args:
            borrower_id: The ID of the entity receiving the loan (Household or Firm).
            amount: The principal amount of the loan.
            interest_rate: The annual interest rate for the loan.
            due_tick: Optional. The simulation tick when the loan is due. If None, it's an open-ended loan.

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

    def issue_treasury_bonds_synchronous(self, issuer: Any, amount_to_raise: float, current_tick: int) -> bool:
        """
        Issues bonds and attempts to settle them immediately via SettlementSystem.
        Returns True if full amount raised, False otherwise.
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
```
