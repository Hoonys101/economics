# Transaction Schema Migration - Architectural Insight Report

## Architectural Insights

### 1. Zero-Sum Integrity Enforcement (Penny Standard)
The `Transaction` model (`simulation/models.py`) and database schema (`simulation/db/schema.py`) have been strictly migrated to enforce `total_pennies` as a required, non-nullable field.
*   **Model**: `total_pennies: int` is now a mandatory field in `Transaction` dataclass (no default value). This forces all call sites to explicitly calculate the total value in pennies at instantiation time.
*   **Database**: `transactions.total_pennies` column is now `INTEGER NOT NULL`.
*   **Handlers**: All transaction handlers (`Goods`, `Labor`, `Stock`, `Financial`, etc.) have been refactored to remove legacy fallback logic (calculating value from `price` float). They now exclusively use `tx.total_pennies` as the Single Source of Truth (SSoT).

### 2. Elimination of Floating-Point Ambiguity
By removing the fallback logic that relied on `round_to_pennies(price * quantity * 100)`, we eliminated a class of bugs where `price` was ambiguous (sometimes dollars, sometimes pennies). Now, `total_pennies` explicitly represents the settlement amount.
*   **Labor Market**: Fixed potential wage calculation errors where `int(tx.price)` was used directly (potentially undercounting wages by 100x if price was dollars). Now uses `trade_value` (total_pennies).
*   **Stock Market**: Updated `StockTransactionHandler` to correctly derive acquisition price in pennies from `total_pennies` for `Portfolio.add`.
*   **Financial Engines**: Fixed critical regressions where financial engines (Debt, Liquidation, Booking) were inflating transaction values by 100x due to incorrect migration assumptions. Verified that inputs to these engines are already in pennies.

### 3. Automated Codebase Migration
A migration script (`scripts/migrate_transaction_calls.py`) was used to refactor over 180 instantiations of `Transaction` across the codebase, ensuring they include the `total_pennies` argument (calculated as `int(price * quantity * 100)` where missing). Manual fixes were applied to tests where specific penny values were required.

## Test Evidence

### Wave 3.2 Final Verification (4 Key Scenarios)
Verification of strict financial integrity and rounding logic.

```
$ python3 scripts/verification/verify_wave_3_2_scenarios.py

--- Testing Atomic Housing Settlement ---
PASS: Sum check: 2000000 + 8000000 == 10000000

--- Testing Dividend Residuals ---
CHECK: Distributed 9999. Residual 1 penny.
PASS: Dividend Residuals: 1 penny stays in wallet (only 9999 distributed).

--- Testing Fractional Interest ---
PASS: Fractional Interest: 0 pennies (Expected: 0)

--- Testing Penny-Perfect Debt Servicing ---
PASS: Interest calculated: 15 pennies (Expected: 15)
 ....
----------------------------------------------------------------------
Ran 4 tests in 0.004s

OK
```

### Full Test Suite Run (Unit + Integration)
Verified clean pass on all relevant modules.

```
$ python3 -m pytest tests/unit/ tests/integration/
...
======================= 690 passed, 1 skipped, 8 warnings in 9.34s =======================
```
