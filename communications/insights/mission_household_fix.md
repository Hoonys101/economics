# Mission Insights: Household Fixes & Integer Precision

## Overview
This mission focused on resolving failures in Household modules and Scenario diagnostics, primarily driven by the migration to integer pennies (`int`) for currency values and DTO field updates.

## Key Changes & Fixes

### 1. DTO Field Updates
- **`EconStateDTO`**: Replaced `labor_income_this_tick` (float) with `labor_income_this_tick_pennies` (int).
- **`HouseholdSnapshotDTO`**: Added `monthly_income_pennies` and `monthly_debt_payments_pennies`.
- **`HouseholdSnapshotAssembler`**: Updated to accept integer arguments matching the new DTO fields.

### 2. Integer Precision in Transaction Logic
- **`TransactionManager`**:
    - Identified a critical bug where `trade_value` (float) was passed to `SettlementSystem` via `government.collect_tax` or direct transfer logic for `labor` transactions.
    - Updated `TransactionManager` to explicitly use `round_to_pennies` for `trade_value` calculation.
    - Updated `execute` logic to convert `trade_value` (pennies) to dollars (float) before invoking `government.calculate_income_tax`, which still operates on floats (dollars).
    - Converted the float result from `calculate_income_tax` back to integer pennies using `round_to_pennies(tax * 100)`.

### 3. Tax Service & Fiscal Policy
- **`TaxService`**:
    - Discovered that `calculate_tax_liability` was returning `int(raw_liability)`, causing truncation of tax amounts (e.g., 16.25 -> 16).
    - Updated `calculate_tax_liability` to return `float` (dollars), preserving precision for the caller (TransactionManager) to handle rounding/conversion.
- **`FiscalPolicyManager`**:
    - Verified that tax brackets are absolute values based on `survival_cost` calculated at initialization.
    - Note: `survival_cost` depends on `HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK` (2.0) and initial `basic_food` price (5.0 or 10.0 depending on data availability).

### 4. Test Corrections
- **Wallet Float Usages**: Fixed multiple tests (`test_stress_scenarios.py`, `test_phase20_scaffolding.py`, `test_td194_integration.py`, `test_government.py`, `test_tax_incidence.py`) passing float values to `wallet.add` or `deposit`. Converted these inputs to integer pennies (e.g., `1000.0` -> `100000`).
- **Assertion Updates**: Updated test assertions to expect integer values (pennies) or adjusted expectations based on corrected tax calculations.
- **Mock Adjustments**: Updated mocks for `EconStateDTO` to include `shadow_reservation_wage_pennies` and `current_wage_pennies`.

## Technical Debt & Insights
- **Unit Mismatch**: There is persistent friction between `TransactionManager` (handling pennies for settlement) and `TaxService`/`Government` methods (expecting dollars for calculation). The explicit conversion in `TransactionManager` is a bridge, but a full migration of `TaxService` to pennies would be cleaner.
- **Mock Consistency**: Many unit tests use `MagicMock` without full spec compliance or with legacy attribute names (`assets` as float instead of `wallet`). This requires careful updating when underlying contracts change.
- **Configuration Ambiguity**: Config values like `TAX_BRACKETS` or `WEALTH_TAX_THRESHOLD` are implicitly dollars, requiring conversion when comparing against penny-based state. This implicit assumption is a source of bugs.

## Conclusion
The fixes enforce strict integer precision for settlement while maintaining the logic of progressive tax calculations (which require float precision for brackets). The `Household` and `Scenario` modules are now aligned with the new architectural guardrails.
