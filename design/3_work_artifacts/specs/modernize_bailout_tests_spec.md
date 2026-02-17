# Spec: Modernize Bailout & DTO Signature Tests

## 1. Introduction
- **Goal**: Resolve Technical Debt `TD-DTO-DESYNC-2026` (BorrowerProfileDTO signature mismatch) and modernize `BailoutCovenant` usage in integration tests.
- **Scope**: `modules/finance/api.py`, `tests/integration/test_finance_bailout.py`, and related mock factories.
- **Context**: Strict DTO enforcement is breaking legacy tests that assume loose dictionary-like behavior or outdated fields.

## 2. API Changes (Source of Truth)

### 2.1. `BorrowerProfileDTO`
- **Change**: Add `borrower_id: AgentID` field.
- **Reason**: Tests instantiate this DTO with `borrower_id` as the first argument. Adding it explicitly aligns the Dataclass definition with usage and makes the DTO self-contained for logging/debugging.

### 2.2. `BailoutCovenant`
- **Status**: No API change needed, but stricter enforcement.
- **Mapping**:
  - Legacy `executive_salary_freeze` (removed) -> Mapped to `executive_bonus_allowed` (False) in tests.
  - Legacy `share_buyback_ban` (removed) -> Covered by `dividends_allowed` (False) or future `treasury_stock_allowed` field.

## 3. Test Refactoring Plan

### 3.1. `tests/integration/test_finance_bailout.py`
- **Objective**: Fix `AttributeError: 'BailoutCovenant' object has no attribute 'executive_salary_freeze'`.
- **Refactoring Logic**:
  ```python
  # OLD
  # assert command.covenants.executive_salary_freeze is True

  # NEW
  assert command.covenants.executive_bonus_allowed is False
  ```
- **Instantiation Fixes**: Ensure `GrantBailoutCommand` mocks use the updated `BailoutCovenant` dataclass.

### 3.2. `BorrowerProfileDTO` Usage
- **Objective**: Fix `TypeError: __init__() got an unexpected keyword argument 'borrower_id'`.
- **Action**: Update all test mock creations to include `borrower_id`.
- **Target Files**: `tests/unit/modules/finance/test_credit_scoring.py` (if exists), `tests/integration/test_bank_operations.py`.

## 4. Verification & Validation

### 4.1. New Test Cases
- Verify `BorrowerProfileDTO` can be instantiated with `borrower_id`.
- Verify `BailoutCovenant` correctly serializes restrictions.

### 4.2. Impact Analysis
- **Risk**: Adding a mandatory field `borrower_id` to `BorrowerProfileDTO` will break code that constructs it *without* an ID.
- **Mitigation**: Grep for `BorrowerProfileDTO(` usage and update all call sites. Default `borrower_id` to a placeholder if strictly necessary, but prefer explicit ID.

## 5. Mocking Strategy
- **Strict Protocol**: Use `MagicMock(spec=BorrowerProfileDTO)` or real instances.
- **Golden Data**: Update `tests/utils/factories.py` to produce valid `BorrowerProfileDTO` instances with `borrower_id`.

## 6. Mandatory Reporting
- Report findings to `communications/insights/modernize-bailout-tests.md`.
- Include specific diffs of fixed DTOs.
