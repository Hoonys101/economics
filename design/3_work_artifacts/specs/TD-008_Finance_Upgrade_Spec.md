```markdown
# Zero-Question Spec: TD-008 - Finance System Upgrade & Refactoring

**ID:** TD-008
**Author:** Gemini (Administrative Assistant)
**Reviewer:** Antigravity (Team Leader)
**Subject:** Refactoring of Bailout Mechanisms and Verification of Solvency Checks

---

## 1. Executive Summary

Based on the **Pre-flight Audit Report (TD-008)**, this task is a **refactoring and verification** effort, not new feature development. The core functionalities for Altman Z-Score evaluation and bailout loans are already implemented.

The primary objectives are:
1.  **Formalize Bailout Covenants**: Replace the `dict` structure in `BailoutLoanDTO` with a formal `BailoutCovenant` class for type safety and clarity.
2.  **Verify & Document Solvency Logic**: Review and document the existing Altman Z-Score implementation to ensure correctness and maintainability.
3.  **Uphold Architectural Integrity**: Ensure all changes respect the existing delegation pattern (`FinanceSystem` -> `Firm.FinanceDepartment`) and do not introduce regressions, particularly money creation/destruction bugs.

## 2. Task 1: Formalize Bailout Covenants (Refactoring)

### 2.1. Objective
Improve type safety and code clarity by replacing the dictionary-based covenant definition with a dedicated `BailoutCovenant` class.

### 2.2. Pseudo-code & Implementation Steps

1.  **Define `BailoutCovenant` Class**:
    *   In `modules/finance/api.py`, create a new `dataclass` or `TypedDict` named `BailoutCovenant`.
    *   It must contain the following fields currently defined as a dictionary in `FinanceSystem.grant_bailout_loan`:
        *   `dividends_allowed: bool`
        *   `executive_salary_freeze: bool`
        *   `mandatory_repayment: float`

2.  **Update `BailoutLoanDTO`**:
    *   In `modules/finance/api.py`, modify the `BailoutLoanDTO` definition.
    *   Change the type of the `covenants` attribute from `Dict[str, Any]` to `BailoutCovenant`.

3.  **Update `FinanceSystem.grant_bailout_loan`**:
    *   In `modules/finance/system.py`, inside the `grant_bailout_loan` method:
    *   Instead of creating a dictionary, instantiate the new `BailoutCovenant` class.
    *   Assign this new object to the `covenants` field when creating the `BailoutLoanDTO`.

## 3. Task 2: Verify & Document Altman Z-Score

### 3.1. Objective
Ensure the existing solvency evaluation logic is correct, robust, and clearly documented. No new implementation is required.

### 3.2. Pseudo-code & Implementation Steps

1.  **Locate and Analyze `calculate_altman_z_score`**:
    *   The method is located in `simulation/components/finance_department.py`.
    *   Analyze its implementation against standard Altman Z-Score formulas for non-manufacturers.
    *   Verify that it correctly uses the firm's financial data (e.g., total assets, retained earnings, etc.).

2.  **Add Comprehensive Docstrings**:
    *   In `simulation/components/finance_department.py`, add a Google-style docstring to `calculate_altman_z_score` explaining:
        *   The exact formula being used.
        *   The source of each variable in the formula.
        *   The meaning of the returned score.
    *   In `modules/finance/system.py`, enhance the docstring for `evaluate_solvency` to clarify:
        *   The two distinct evaluation paths (runway for startups, Z-Score for established firms).
        *   The thresholds used (`STARTUP_GRACE_PERIOD_TICKS`, `ALTMAN_Z_SCORE_THRESHOLD`) and their source (`config_module`).

## 4. Interface & DTO Specification (`modules/finance/api.py`)

### 4.1. New Class: `BailoutCovenant`
```python
from dataclasses import dataclass

@dataclass
class BailoutCovenant:
    """
    Defines the restrictive conditions attached to a bailout loan.
    """
    dividends_allowed: bool
    executive_salary_freeze: bool
    mandatory_repayment: float # Ratio of profit to be repaid
```

### 4.2. Modified DTO: `BailoutLoanDTO`
```python
# In modules/finance/api.py

@dataclass
class BailoutLoanDTO:
    """
    Data Transfer Object for a bailout loan provided by the government.
    """
    firm_id: int
    amount: float
    interest_rate: float
    covenants: BailoutCovenant # MODIFIED: Changed from Dict to BailoutCovenant class
```

## 5. Verification Plan

### 5.1. Unit & Integration Testing
The implementer (Jules) MUST perform the following checks:

1.  **New Test for `grant_bailout_loan`**:
    *   Create a test that calls `FinanceSystem.grant_bailout_loan`.
    *   **Assert** that the `covenants` attribute of the returned `BailoutLoanDTO` is an instance of `BailoutCovenant`.
    *   **Assert** that the firm's liabilities and cash reserves are updated correctly.
    *   **Assert** that the government's assets are debited correctly.

2.  **Regression Testing (CRITICAL)**:
    *   Execute all existing tests related to `FinanceSystem` and `Firm`.
    *   **Pay special attention to `test_service_debt`**. Verify that no new money creation or destruction bugs are introduced by monitoring the total money supply in the test environment.
    *   Run a baseline simulation and compare firm bankruptcy rates before and after the change to ensure the solvency logic verification did not introduce unintended economic shifts.

## 6. [MANDATORY] Reporting Duty

The implementer (Jules) is required to document any insights, identified technical debt, or suggestions for improvement during this task. All findings must be recorded in a new markdown file and saved to the `communications/insights/` directory.
```
