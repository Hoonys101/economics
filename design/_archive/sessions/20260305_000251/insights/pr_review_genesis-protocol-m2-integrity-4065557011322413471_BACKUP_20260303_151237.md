🕵️  Reviewing Code with instruction: 'Analyze this PR.'...
📖 Attached 30 context files using Smart Context Injector.
📊 [GeminiWorker] Total Context Size: 280.95 kb (287696 chars)
⚠️ Warning: Context exceeds hard limit. Truncating to 256000 chars.
🚀 [GeminiWorker] Running task with manual: git-review.md
🛡️  Memory Guard Active: Limit = 2048MB
📡 [GeminiWorker] Feeding prompt to STDIN (256035 chars)...
✅ [GeminiWorker] STDIN feed complete.

📝 [Review Report]
============================================================
# Code Review Report

### 1. 🔍 Summary
The PR successfully introduces `TransactionMetadataDTO` to replace raw dictionaries in transaction metadata, enforcing data boundary purity. It also delegates M2 calculation directly to the SSoT `MonetaryLedger` and enforces the genesis initialization sequence. However, the PR failed to update test mocks properly for the housing handlers, resulting in 7 failing unit tests, and accidentally included local debug scripts in the commit.

### 2. 🚨 Critical Issues
- **Leftover Debug Scripts**: The developer committed local troubleshooting scripts (`fix_test_mocks.py` and `fix_test.py`). These must be removed from the PR.
- **Broken CI Pipeline**: 7 unit tests (including `test_housing_transaction_success` and `test_handle_disbursement_failure`) are failing. This blocks merging.

### 3. ⚠️ Logic & Spec Gaps
- **Test Suite Regression**: The insight claims to have "Standardized all LienDTO and LoanDTO access... across all production handlers and test factories". However, in `test_housing_transaction_handler.py` and `test_housing_handler.py`, the `context.bank.grant_loan` mock still returns a raw dictionary (e.g., `{"loan_id": "loan_123"}`). When the handler accesses `.loan_id`, it either raises an `AttributeError` or generates a `MagicMock`, causing the final assertions (like `terminate_loan.assert_called_with("loan_123")`) to fail.
- **Exception Masking Catch-All**: In `HousingTransactionHandler`, `except Exception as e` correctly changed to `raise`, which exposed the broken tests. This is a good change, but the developer failed to follow through and fix the tests that surfaced.

### 4. 💡 Suggestions
- **Fix Mocks**: Update the `grant_loan` mocks in the housing tests to return an actual `LoanDTO` or a `MagicMock` where the `loan_id` property is explicitly set to the string `"loan_123"`. 
- **DTO Access Validation**: Ensure that legacy property access (e.g. `lien['lien_type']`) is fully eradicated in the test assertions, not just the handlers.
- **Clean Up**: Remove `fix_test.py` and `fix_test_mocks.py`.

### 5. 🧠 Implementation Insight Evaluation
- **Original Insight**: 
  > "Removed broad exception handlers in market transaction components to expose underlying runtime errors. Standardized all LienDTO and LoanDTO access to use getattr object attributes instead of dictionary keys across all production handlers and test factories."
- **Reviewer Evaluation**: The insight is technically profound and correctly identifies the root cause of silent logical failures (unstructured dictionary metadata and broad exception handlers). Intercepting dict injections at `Transaction.__post_init__` is an elegant pattern for backward compatibility. However, the insight's claim that test factories were completely standardized is demonstrably false, as proven by the 7 failing tests and the developer's abandoned `fix_test_mocks.py` script. The implementation was abandoned halfway.

### 6. 📚 Manual Update Proposal (Draft)
- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Draft Content**:
  ```markdown
  ### [Debt] Legacy Dictionary Injection in Test Mocks
  - **Component**: Unit Tests (`HousingTransactionHandler`, Core Test Mocks)
  - **Description**: Despite migrating to strict DTOs (`TransactionMetadataDTO`, `LienDTO`, `LoanDTO`) in production code, several legacy unit tests still inject raw dictionaries into mocks (e.g., `grant_loan.return_value = ({"loan_id": "loan_123"}, None)`). This causes false negative test failures when handlers attempt object attribute access.
  - **Required Action / Fix**: Audit and refactor all test fixtures and mock return values (specifically in housing and finance tests) to use the canonical DTOs instead of raw dictionaries.
  ```

### 7. ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**

- **Reason**: 7 unit tests are failing due to broken mocks that were not updated alongside the DTO migration. Furthermore, debugging scripts (`fix_test_mocks.py`) were committed to the codebase. Ensure all tests pass and garbage files are removed before resubmission.
============================================================
✅ Review Saved: C:\coding\economics\design\_archive\gemini_output\review_backup_20260303_143128_Analyze_this_PR.md

--- STDERR ---
📉 Budget Tight: Stubbing primary pytest_output.txt
📉 Budget Tight: Stubbing primary simulation/components/engines/finance_engine.py
📉 Budget Tight: Stubbing primary simulation/components/engines/hr_engine.py
📉 Budget Tight: Stubbing primary simulation/firms.py
📉 Budget Tight: Stubbing primary simulation/models.py
📉 Budget Tight: Stubbing primary simulation/systems/bootstrapper.py
🛑 Budget Critical: Metadata-only for primary simulation/systems/handlers/goods_handler.py
🛑 Budget Critical: Metadata-only for primary simulation/systems/handlers/labor_handler.py
🛑 Budget Critical: Metadata-only for primary simulation/systems/inheritance_manager.py
🛑 Budget Critical: Metadata-only for primary simulation/systems/lifecycle/death_system.py
🛑 Budget Critical: Metadata-only for primary simulation/systems/liquidation_manager.py
🛑 Budget Critical: Metadata-only for primary simulation/systems/ministry_of_education.py
🛑 Budget Critical: Metadata-only for primary simulation/systems/settlement_system.py
🛑 Budget Critical: Metadata-only for primary simulation/systems/transaction_processor.py
🛑 Budget Critical: Metadata-only for primary simulation/world_state.py
🛑 Budget Critical: Metadata-only for primary tests/finance/test_monetary_expansion_handler.py
🛑 Budget Critical: Metadata-only for primary tests/unit/markets/test_housing_transaction_handler.py
🛑 Budget Critical: Metadata-only for primary tests/unit/systems/test_inheritance_manager.py
🛑 Budget Critical: Metadata-only for primary tests/unit/systems/test_m2_integrity.py
🛑 Budget Critical: Metadata-only for primary tests/unit/test_labor_thaw.py
🛑 Budget Critical: Metadata-only for primary tests/unit/test_m2_integrity_new.py
🛑 Budget Critical: Metadata-only for primary tests/unit/test_transaction_handlers.py
🛑 Budget Critical: Metadata-only for primary tests/utils/factories.py
