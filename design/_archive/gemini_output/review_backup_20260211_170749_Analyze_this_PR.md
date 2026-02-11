# 🔍 PR Review: Fix Simulation Errors

## 🔍 Summary
This Pull Request addresses a series of test failures that arose from recent refactorings. The fixes primarily involve updating test setups to align with new architectural patterns, such as the move to integer-based currency (`_pennies`) and the dependency injection required for the now-stateless `Bank` module. An excellent insight report accompanies these fixes.

## 🚨 Critical Issues
- **Invalid Python Syntax in Test File**: In `tests/system/test_audit_integrity.py`, file paths have been added as decorators. This is invalid Python syntax and will cause the test runner to crash before any tests are executed. This is a **Hard-Fail** and must be corrected.

  ```python
  // File: tests/system/test_audit_integrity.py
  // Invalid decorator syntax
  @design\_archive\insights\2026-02-11_Final_Test_Failures_And_Patch_Scoping.md('simulation.factories.agent_factory.HouseholdFactory')
  @design\_archive\insights\2026-02-11_Final_Test_Failures_And_Patch_Scoping.md('simulation.systems.demographic_manager.Household')
  @design\_archive\insights\2026-02-11_Final_Test_Failures_And_Patch_Scoping.md('simulation.systems.demographic_manager.create_config_dto')
  def test_birth_gift_rounding(self, mock_create_config, mock_household_cls, mock_household_factory_cls):
      ...
  ```

  These lines appear to be misplaced notes or copy-paste errors and must be removed or converted to comments.

## ⚠️ Logic & Spec Gaps
- No significant logic gaps were identified. The changes correctly adapt the tests to the new realities of the codebase, such as using `amount_pennies` and mocking the `FinanceSystem` for the `Bank`.

## 💡 Suggestions
- **Deprecate Legacy Test Helpers**: The insight report correctly identifies that `Bank.deposit_from_customer` is a legacy method that manually manipulates state. To enforce the stateless nature of the `Bank` proxy, consider marking such methods with `@deprecated` and creating a plan to refactor the tests that rely on them. This will prevent future confusion.

## 🧠 Implementation Insight Evaluation
- **Original Insight**:
  ```markdown
  # Fix Simulation Errors Insight Report

  ## Mission Context
  Resolve simulation-level errors and component mismatches including Bank, FirmRefactor, Audit Integrity, and SalesEngine.

  ## Technical Debt & Insights

  ### 1. Bank Portfolio Integration Test
  - **Issue:** The test `test_bank_deposit_balance` failed because `Bank` is now a stateless proxy delegating to `FinanceSystem`, but the test did not inject a `FinanceSystem`.
  - **Fix:** Mocked `FinanceSystem` and `FinancialLedgerDTO` in the test. Configured `Bank` to use this mock.
  - **Insight:** Tests for `Bank` must now always setup a `FinanceSystem` mock with a valid `Ledger` structure because `Bank` methods rely on `self.finance_system.ledger`. `deposit_from_customer` manually updates the ledger state in the `Bank` class, which is a legacy/test helper that relies on internal ledger structure.

  ### 2. Firm Refactor Test
  - **Issue:** `KeyError: 'amount_pennies'` in `test_firm_refactor.py`.
  - **Fix:** Updated the test to use `amount_pennies` in the `Order` `monetary_amount` dictionary.
  - **Insight:** The `Order` object construction in tests was outdated. It used `amount` (float) while the system now expects `amount_pennies` (int) for strict integer precision.

  ### 3. Audit Integrity Test
  - **Issue:** `No transfer call detected` in `test_birth_gift_rounding`.
  - **Fix:** Patched `HouseholdFactory` in `tests/system/test_audit_integrity.py` to ensure `create_newborn` returns a mock object instead of failing silently (swallowed exception in `DemographicManager`).
  - **Insight:** `DemographicManager` swallows exceptions during birth processing, which makes debugging test failures hard. The test environment must fully mock dependencies like `HouseholdFactory`.

  ### 4. Sales Engine Test
  - **Issue:** `test_generate_marketing_transaction` failed (returned `None`) because it set `marketing_budget` (float) on `SalesState` which only uses `marketing_budget_pennies` (int).
  - **Fix:** Updated the test to set `marketing_budget_pennies`.
  - **Insight:** `SalesState` and other state DTOs are strict about integer fields (`_pennies`). Tests must not use legacy float attributes.

  ### 5. Integer Precision Guardrail
  - **Observation:** `Bank` and other legacy components still accept `float` in some method signatures (e.g., `deposit_from_customer`) but cast to `int` internally. Tests often use `float` for assertions.
  - **Action:** Updated tests to assert integer values where appropriate to align with the Integer Precision guardrail.
  ```
- **Reviewer Evaluation**: **Excellent**. The report is clear, detailed, and provides valuable, code-grounded insights. The identification of silent exception swallowing in `DemographicManager` is a particularly important piece of technical debt to have recorded. The report correctly diagnoses each issue and documents the lesson learned, fulfilling the requirements perfectly.

## 📚 Manual Update Proposal
The insight regarding the `DemographicManager` is critical for future debugging and test writing. It should be added to the project's central technical debt ledger.

- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**:
  ```markdown
  ## Testing & Debugging
  | ID | 현상 (Symptom) | 원인 (Cause) | 해결책 (Solution) | 교훈 (Lesson) | 담당자 | 상태 |
  |---|---|---|---|---|---|---|
  | TDL-0XX | Tests involving agent creation fail silently without clear errors. | The `DemographicManager` swallows exceptions during birth processing, hiding the root cause of failures (e.g., incomplete mocks). | Ensure test environments fully mock all dependencies, such as the `HouseholdFactory`, to prevent the manager from entering a failing state. | Frameworks that silently handle exceptions make debugging extremely difficult. Tests must be fully isolated with complete mock setups to be reliable. | [Your Name] | Identified |
  ```

## ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**

While the logic fixes and insight reporting are excellent, the introduction of a critical syntax error in `tests/system/test_audit_integrity.py` prevents approval. Please remove the invalid decorator syntax and resubmit.
