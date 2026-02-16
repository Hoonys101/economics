# modules/finance/api.py

```python
from dataclasses import dataclass
from typing import List, Optional, Protocol, Tuple, Union, Any

# =============================================================================
# DTO Definitions (Strict Dataclasses)
# =============================================================================

@dataclass(frozen=True)
class BorrowerProfileDTO:
    """
    Data Transfer Object representing a borrower's financial profile.
    Immutable to ensure data integrity during credit assessment.
    """
    gross_income: float
    existing_debt_payments: float
    collateral_value: float
    credit_score: Optional[int] = None
    employment_status: str = "UNKNOWN"
    # Added for context; often used in legacy dicts
    preferred_lender_id: Optional[str] = None

@dataclass(frozen=True)
class LoanInfoDTO:
    """
    Data Transfer Object representing the state of a loan.
    """
    loan_id: str
    borrower_id: str
    original_amount: float
    outstanding_balance: float
    interest_rate: float
    origination_tick: int
    due_tick: Optional[int]
    status: str = "ACTIVE"
    term_ticks: int = 360  # Default term if not specified

@dataclass(frozen=True)
class CreditAssessmentResultDTO:
    """
    Result of a credit scoring assessment.
    """
    is_approved: bool
    max_loan_amount: float
    reason: Optional[str]

@dataclass(frozen=True)
class DebtStatusDTO:
    """
    Summary of a borrower's debt situation.
    """
    borrower_id: str
    total_outstanding_debt: float
    loans: List[LoanInfoDTO]
    is_insolvent: bool
    next_payment_due: Optional[float]
    next_payment_due_tick: Optional[int]

# =============================================================================
# Interfaces / Protocols
# =============================================================================

class ICreditScoringService(Protocol):
    def assess_creditworthiness(
        self, 
        profile: BorrowerProfileDTO, 
        requested_loan_amount: float
    ) -> CreditAssessmentResultDTO:
        ...

class IBankService(Protocol):
    def grant_loan(
        self, 
        borrower_id: str, 
        amount: int, 
        interest_rate: float, 
        due_tick: Optional[int] = None, 
        borrower_profile: Optional[BorrowerProfileDTO] = None
    ) -> Optional[Tuple[LoanInfoDTO, Any]]: # Any = Transaction
        ...
        
    def get_debt_status(self, borrower_id: str) -> DebtStatusDTO:
        ...

# ... (Other interfaces like IFinanceSystem omitted for brevity but implied)
```

# design/3_work_artifacts/specs/fix-dto-subscripting_spec.md

```markdown
# Specification: Finance & Credit DTO Purity Refactoring

## 1. Overview
**Goal**: Eliminate `TypeError: '...' object is not subscriptable` runtime errors by enforcing Dot-Notation access for `BorrowerProfileDTO` and `LoanInfoDTO` across the codebase.
**Scope**: `modules/finance`, `simulation/bank.py`, `simulation/loan_market.py`, and related tests.

## 2. Root Cause Analysis
- **Migration Lag**: The system recently migrated `LoanInfoDTO` and `BorrowerProfileDTO` from standard dictionaries (or `TypedDict`) to `dataclasses`.
- **Legacy Access**: Consumers in `CreditScoringService` and `Bank` are still using dictionary syntax (`['key']`), which causes immediate runtime failures with Dataclasses.
- **Test Gap**: Unit tests were mocking these DTOs as dictionaries or loose mocks without strict spec compliance, masking the issue until integration.

## 3. Implementation Plan

### 3.1. `modules/finance/credit_scoring.py`
**Changes**:
- Update `assess_creditworthiness` method.
- **Refactoring**:
  - `profile["gross_income"]` -> `profile.gross_income`
  - `profile["existing_debt_payments"]` -> `profile.existing_debt_payments`
  - `profile["collateral_value"]` -> `profile.collateral_value`
- **Safety**: Ensure `profile` input is strictly typed as `BorrowerProfileDTO`.

### 3.2. `simulation/bank.py`
**Changes**:
- Update `grant_loan`:
  - Ensure `borrower_profile` passed to `process_loan_application` is a Dataclass instance. If a dict is received (from legacy callers), convert it to `BorrowerProfileDTO` immediately.
  - Fix `loan_dto` handling: Remove `SimpleNamespace` hack if `loan_dto` is guaranteed to be a Dataclass from `FinanceSystem`. If hybrid, usage of `getattr` might be a temporary bridge, but explicit attribute access is preferred.
- Update `get_debt_status`:
  - Fix generator expression: `sum(l['outstanding_balance'] for l in loans)` -> `sum(l.outstanding_balance for l in loans)`.
  - Fix list comprehension for `loans` in return DTO if necessary.

### 3.3. `simulation/loan_market.py`
**Changes**:
- Review `evaluate_mortgage_application`.
- **Note**: `MortgageApplicationDTO` usage (`application.get(...)`) suggests it might still be a `TypedDict`.
- **Decision**: 
  - If `MortgageApplicationDTO` is a Dataclass: Replace `.get()` with `getattr(application, 'field', default)`.
  - If `MortgageApplicationDTO` is a Dict: **No change required** for this specific file unless we standardize it to a Dataclass now.
  - *Instruction*: Inspect `modules/finance/api.py` definitions during implementation. If it's a Dataclass, fix accesses.

### 3.4. `tests/unit/finance/test_bank_service_interface.py`
**Changes**:
- Update `test_grant_loan`:
  - Assertions: `loan_info['borrower_id']` -> `loan_info.borrower_id`.
- Update `test_get_debt_status`:
  - Assertions: `status['total_outstanding_debt']` -> `status.total_outstanding_debt`.

## 4. Verification & Testing Strategy

### 4.1. Unit Tests
- **Run**: `pytest tests/unit/finance/test_bank_service_interface.py`
- **Run**: `pytest tests/unit/finance/test_credit_scoring.py`
- **Constraint**: Verify tests pass without `TypeError`.

### 4.2. Mock Integrity
- When mocking `LoanInfoDTO` in tests, **do not** use a simple dict. Instantiate the actual Dataclass.
- Example:
  ```python
  # CORRECT
  loan_dto = LoanInfoDTO(loan_id="1", ...)
  
  # INCORRECT
  loan_dto = {"loan_id": "1", ...}
  ```

## 5. Risk Assessment (Pre-Implementation Audit)

### 🚨 Critical Risks
1. **Hybrid Consumers**: External scripts or untyped agents might still be passing dictionaries to `Bank.grant_loan`.
   - **Mitigation**: Add a sanitation layer at the entry of `Bank.grant_loan` that attempts to convert `dict` -> `BorrowerProfileDTO` if `isinstance(profile, dict)` checks true.
2. **`MortgageApplicationDTO` Ambiguity**: If this DTO is mixed (dict in some places, object in others), partial fixes will cause regression.
   - **Mitigation**: Check definition. If `TypedDict`, keep dict access. If `Dataclass`, fix all access.

### 📝 Mandatory Reporting
- Upon completion, you must document the DTO standardization status of `MortgageApplicationDTO` and any remaining dict usages in `communications/insights/fix-dto-subscripting.md`.
```