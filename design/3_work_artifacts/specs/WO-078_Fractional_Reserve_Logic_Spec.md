# Work Order: - Fractional Reserve Banking

**Phase:** 2
**Priority:** HIGH
**Prerequisite:** (IBankService Definition)

## 1. Problem Statement
The current economic model lacks a realistic credit creation mechanism. Loans are implicitly drawn from existing capital, preventing the simulation of money supply expansion and its effects on inflation, asset prices, and economic growth. A fractional reserve banking system is required to model how commercial banks create new money through lending.

## 2. Objective
Implement a fractional reserve banking system where commercial banks can create new deposit money (credit) when issuing loans, constrained by a central reserve requirement, and assess borrower creditworthiness using standard financial metrics (DTI/LTV).

## 3. Core Concepts

* **Fractional Reserve Banking**: A system where banks hold only a fraction of their deposit liabilities in liquid reserves and lend out the remainder.
* **Credit Creation (Money Multiplier)**: When a bank grants a loan, it creates a new loan asset and a corresponding new deposit liability for the borrower. This new deposit is 'new money' created within the banking system.
* **Debt-to-Income (DTI)**: A metric comparing a borrower's total monthly debt payments to their gross monthly income. Used to assess repayment ability.
* **Loan-to-Value (LTV)**: A metric comparing the loan amount to the appraised value of the asset being purchased (collateral). Used to assess risk in secured loans.
* **Bank Solvency**: The bank's ability to meet its obligations. In this context, it refers to maintaining reserves equal to or greater than the `reserve_requirement * total_deposits`.

## 4. Detailed Design & Implementation Plan

This design explicitly addresses the risks identified in the `Pre-flight Audit Report: `.

### Track A: Implement `CreditScoringService`
To avoid circular dependencies and adhere to the Single Responsibility Principle, credit risk assessment will be delegated to a new, dedicated service.

- **Action**: Create a new interface `ICreditScoringService` in `modules/finance/api.py`.
- **Action**: Create an implementation class `CreditScoringService` in `modules/finance/credit_scoring.py`.
- **Logic**:
 1. The service's primary method, `assess_creditworthiness`, will accept a `BorrowerProfileDTO`.
 2. It will calculate DTI and LTV based on the DTO's data and configurable thresholds in `config/finance.yaml`.
 3. It returns a `CreditAssessmentResultDTO` containing `is_approved: bool` and a risk score.

### Track B: Update `Bank` (IBankService Implementation)
The `Bank` class will be refactored to orchestrate the lending process, focusing on reserve management and credit creation.

- **Location**: `modules/finance/bank.py` (or the concrete class implementing `IBankService`).
- **Dependencies**: The `Bank` will be injected with an `ICreditScoringService`.
- **Updated `grant_loan` Logic**:
 1. The `grant_loan` method will now accept a `BorrowerProfileDTO` alongside other parameters.
 2. **Step 1: Credit Assessment**: Call `self.credit_scoring_service.assess_creditworthiness(borrower_profile)`. If not approved, return `None`.
 3. **Step 2: Solvency Check**:
 - Calculate `required_reserves = self.get_total_deposits() * config.RESERVE_REQUIREMENT`.
 - Check if `self.get_reserves() > required_reserves`.
 - If the bank is insolvent or granting the loan would make it insolvent, the loan is rejected. Return `None`.
 4. **Step 3: Credit Creation**:
 - Create the `Loan` object (internal asset).
 - **Critically, create a new deposit for the borrower by calling `self.deposit(borrower_id, amount)`. This is the act of creating new money.**
 - The bank's balance sheet expands: assets (new loan) and liabilities (new deposit) both increase.
 5. **Step 4: Return DTO**: Return a `LoanInfoDTO` for the newly created loan.

### Track C: Refactor Agent Tests for Dependency Injection
To mitigate breaking existing tests, agent-level tests will be updated to use dependency injection for banking services.

- **Action**: Audit `tests/household/` and `tests/firm/` for any direct instantiation of `Bank`.
- **Refactoring**:
 - Modify test function signatures to accept a mocked `IBankService` fixture.
 - Use `pytest-mock` to provide a `mocker.MagicMock(spec=IBankService)` instance.
 - Configure the mock's methods (`grant_loan`, `get_balance`, etc.) in each test to simulate desired banking outcomes. This decouples agent tests from the bank's internal logic.

## 5. Verification & Testing

- **Unit Tests (`tests/finance/test_credit_scoring.py`)**:
 - Test `CreditScoringService` with various `BorrowerProfileDTO` inputs to verify correct DTI/LTV calculation and approval logic.
- **Unit Tests (`tests/finance/test_bank.py`)**:
 - Test `Bank.grant_loan` method.
 - Mock `ICreditScoringService` to return "approved".
 - Verify that when a loan is granted, the bank's total deposits and total loan assets increase by the loan amount.
 - Verify that a loan is rejected if the reserve requirement is not met.
- **Integration Tests**:
 - A test simulating a `Household` agent applying for a loan from a `Bank`, which uses the real `CreditScoringService`.

## 6. Jules Assignment
| Track | Task | 파일 |
|---|---|---|
| A | Define and Implement `ICreditScoringService` & DTOs. | `modules/finance/api.py`, `modules/finance/credit_scoring.py` |
| B | Refactor `Bank.grant_loan` to use `CreditScoringService` and perform credit creation. | `modules/finance/bank.py` |
| C | Audit and refactor agent tests to use Dependency Injection for `IBankService`. | `tests/household/`, `tests/firm/` |

---
## 7. Risk & Impact Audit (Mitigation Plan)

- **Circular Dependencies**: **Mitigated.** The `Bank` will not import `Household` or `Firm`. It will operate on a `BorrowerProfileDTO` provided by the agent, and credit decisions are delegated to `CreditScoringService`.
- **SRP Violation**: **Mitigated.** The `Bank` is no longer responsible for credit analysis. Its role is correctly limited to reserve management and the mechanics of creating loans and deposits.
- **God Class**: **Mitigated.** The logic is contained within the `IBankService` implementation, cleanly separating commercial banking (credit creation) from `IFinanceSystem` (sovereign finance).
- **Test Breakage**: **Mitigated.** Track C explicitly allocates work to refactor agent tests, replacing direct `Bank` instantiation with dependency injection, ensuring the test suite remains robust.

---
## 8. API Additions for `modules/finance/api.py`

```python
# Add these new DTOs and the new Interface to modules/finance/api.py

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
```
