# Deep Root Cause Profile

## Executive Summary
This audit identifies three critical systemic failures causing the reported financial discrepancies. The primary "Tick 1 Deletion" (-185k) is a false positive leak caused by an accounting definition error where Government assets were excluded from the Money Supply (M2) calculation. The "Lifecycle Errors" are caused by a type error in the `TransactionProcessor`, preventing tax collection and leading to statistical drift. The "+293.3120 Anomaly" is a result of consistent money creation flow that appears as a leak due to the same accounting definition error or minor floating-point accumulation in interest payments.

## 1. Tick 1 Deletion (-185,430.00)
- **Status**: Identified
- **Root Cause**: **Accounting Definition Error**.
    - The `WorldState.calculate_total_money()` method explicitly excludes `Government.assets` from the M2 calculation.
    - At Tick 1, the `MinistryOfEducation` executes the "Public Education" logic.
    - Households pay "Student Share" of education costs to the Government.
    - **Mechanism**: Money moves from `Households` (Inside M2) to `Government` (Outside M2).
    - **Result**: M2 decreases by the total student share amount (~185k), which the system flags as a "Leak" because it is not recorded as "Money Destruction".
- **Fix**: Update `WorldState.calculate_total_money()` to include `state.government.assets`. This recognizes the Government as an economic actor holding liquidity, ensuring transfers to/from the government satisfy zero-sum conservation.

## 2. Systemic Money Destruction (Lifecycle/Tax Errors)
- **Status**: Identified
- **Root Cause**: **Type Error in TransactionProcessor**.
    - The `TransactionProcessor` calls `government.collect_tax(..., payer_id, ...)` passing the agent's **ID** (int/str) instead of the **Agent Object**.
    - `TaxAgency.collect_tax` expects an object to verify `hasattr(payer, 'id')`.
    - **Mechanism**: `collect_tax` logs "Payer X is not an object" and returns 0.0, failing to record tax statistics or execute `FinanceSystem` logic (if connected).
    - **Result**: While the `SettlementSystem` successfully transfers the funds (via `TransactionProcessor`'s direct call), the statistical tracking of tax revenue fails, leading to discrepancies between "Collected Tax" and actual asset movements.
- **Fix**: Update `TransactionProcessor` to pass the `buyer` or `seller` object itself to `government.collect_tax`, not just the ID.

## 3. The +293.3120 Anomaly
- **Status**: Identified
- **Root Cause**: **M2 Exclusion of Government & Infrastructure**.
    - Similar to the Tick 1 error, the Government invests in Infrastructure (~5000/tick) by paying the `EconomicRefluxSystem`.
    - **Mechanism**: `Government` (Outside M2) pays `RefluxSystem` (Inside M2).
    - **Result**: M2 **increases** by the investment amount. This should appear as a positive leak.
    - The specific value `293.3120` suggests a net effect of multiple flows (e.g., Infrastructure + Interest - Tax). If Tax leaks (negative) and Infrastructure adds (positive), the net result is the anomaly.
    - Once Government is added to M2, all these flows become internal transfers, eliminating the "Leak" noise.

## 4. De-registration Bug
- **Status**: Clarified
- **Root Cause**: The reported "De-registration" issue is largely the symptom of the `TaxAgency` Type Error described above. When `TransactionProcessor` fails to handle the object/ID distinction, it manifests as "Payer not found" errors that worsen when agents die (as IDs might be reused or lookups fail, though the primary error is the Type mismatch).
- **Fix**: The fix for #2 addresses the root cause. No complex de-registration logic is needed beyond what `LifecycleManager` already does (rebuilding `state.agents`), provided the `TransactionProcessor` uses valid object references from the current state.
