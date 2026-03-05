# WO-WAVE6-RESTORATION-SPEC: Architectural Insights & Regression Analysis

## 1. Architectural Insights

### Tooling Restoration (ContextInjectorService)
The restoration of `ContextInjectorService` in `dispatchers.py` was implemented using a lazy import strategy (inside the `execute` method). This was necessary to resolve a circular dependency between `registry.api` and `context_injector.service`. This pattern ensures that the heavyweight dependency injection machinery is only loaded when a mission is actually dispatched, improving startup time for other commands and preventing import loops.

### SSoT Enforcement (Penny Standard)
The enforcement of the "Penny Standard" Single Source of Truth (SSoT) required significant updates to `SettlementSystem` and `TaxationSystem`.
- **SettlementSystem**: Now constructs `Transaction` objects where `price` is strictly a display value (Dollars) and `total_pennies` is the SSoT. This aligns with the `Transaction` model's `__post_init__` logic.
- **TaxationSystem**: Was previously relying on `int(quantity * price)` which, due to the Dollar/Penny ambiguity in `price`, was calculating tax on 1% of the actual value (treating Dollars as Pennies). By switching to `transaction.total_pennies`, the tax calculation is now mathematically correct and robust.

### Default Transfer Handler
The `DefaultTransferHandler` was introduced to capture generic `transfer` transactions. This closes a gap where system-level transfers (e.g., grants, minting) were not being processed by the `TransactionProcessor` pipeline, potentially missing audit logs or side-effects.

## 2. Regression Analysis

### Broken Tests & Fixes
Several tests failed due to the SSoT enforcement, revealing that they were relying on the previous incorrect behavior or ambiguous data models.

1.  **`tests/unit/systems/test_settlement_system.py::test_transfer_success`**
    -   **Issue**: Expected `tx.quantity` to match the transfer amount (20).
    -   **Fix**: Updated expectation to `tx.quantity == 1.0` and `tx.total_pennies == 20`, reflecting the new Transfer schema.

2.  **`tests/unit/test_transaction_integrity.py::test_settlement_system_record_total_pennies`**
    -   **Issue**: Expected `tx.quantity` to be 100.
    -   **Fix**: Updated to expect `tx.quantity == 1.0` and `tx.price == 1.0` (100 pennies = $1.00).

3.  **`tests/system/test_engine.py::TestSimulation::test_process_transactions_labor_trade`**
    -   **Issue**: Test expected `tax_pennies = 2` (0.1% effective rate) on a 2000 penny transaction. This was due to the bug where tax was calculated on the Dollar value (20) treated as pennies.
    -   **Fix**: Updated expectation to `tax_pennies = 200` (10% of 2000 pennies), reflecting the correct tax calculation.

4.  **`tests/unit/test_tax_incidence.py` (Household & Firm Payer Scenarios)**
    -   **Issue**: Tests hardcoded an expected tax of `1625` pennies on a `1,000,000` penny transaction. This `1625` was derived from calculating progressive tax on `10,000` (the Dollar value).
    -   **Fix**: Updated expectation to `199,625` pennies, which is the correct progressive tax on `1,000,000` pennies. This confirms the fix in `TaxationSystem` is working correctly.

## 3. Test Evidence

The entire test suite passed after applying the fixes.

```
================= 1033 passed, 11 skipped, 1 warning in 10.33s =================
```
