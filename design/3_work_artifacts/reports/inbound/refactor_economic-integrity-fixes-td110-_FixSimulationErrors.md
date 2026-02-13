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