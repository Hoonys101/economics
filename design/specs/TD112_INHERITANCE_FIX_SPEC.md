# Spec: TD-112 Inheritance Integer Distribution

## 1. Objective
Implement a high-fidelity, integer-based asset distribution system for the `InheritanceManager` to eliminate floating-point precision errors, prevent asset leakage, and ensure that all remainders are correctly allocated to an heir instead of being lost or confiscated.

## 2. Background & Problem
The current `InheritanceManager.process_death` method uses float-based arithmetic for distributing cash and stock assets among heirs. This approach has two critical flaws:

1.  **Precision Loss**: Floating-point division (`total / num_heirs`) can introduce minute precision errors, causing asset "dust" to be created or lost. This violates the simulation's zero-sum integrity.
2.  **Incorrect Residual Handling**: The current cash distribution logic rounds down each heir's share and transfers the leftover "residual" (rounding remainder) to the government. This is incorrect; the full inheritance should be distributed to the designated heirs. The stock distribution logic has no residual handling at all, leading to potential loss of fractional shares.

This work order (TD-112) directs the refactoring of the distribution logic to use integer-based accounting for both cash (pennies) and stocks.

## 3. Proposed Solution (Pseudo-code)
The new logic will be applied within `InheritanceManager.process_death`, specifically in the "Distribution (Transfer)" section, replacing the existing cash and stock distribution loops.

### 3.1. Cash Distribution (Integer-based)

This logic replaces the section starting at `line 259`.

```python
# In InheritanceManager.process_death, after tax payment

# A. Cash Distribution (Integer-based)
# ==========================================================
total_cash = deceased.assets
if total_cash > 0 and heirs:
    num_heirs = len(heirs)

    # 1. Convert to integer (pennies) for precise calculation
    total_pennies = int(total_cash * 100)

    # 2. Calculate base share and remainder
    pennies_per_heir = total_pennies // num_heirs
    remainder_pennies = total_pennies % num_heirs

    cash_share = pennies_per_heir / 100.0

    # 3. Distribute base share to all heirs
    for i, heir in enumerate(heirs):
        # The last heir gets the remainder
        if i == num_heirs - 1:
            final_share = (pennies_per_heir + remainder_pennies) / 100.0
            if final_share > 0:
                settlement.transfer(deceased, heir, final_share, f"inheritance_share_final:{deceased.id}")
        else:
            if cash_share > 0:
                settlement.transfer(deceased, heir, cash_share, f"inheritance_share:{deceased.id}")
    
    # 4. Remove residual capture logic. The deceased's assets should now be zero.
    # The block `if deceased.assets > 0: settlement.transfer(deceased, government, ...)`
    # MUST BE REMOVED.
```

### 3.2. Stock Distribution (Integer-based)

This logic replaces the section starting at `line 280`. It must handle indivisible shares by distributing whole shares and giving the remainder to heirs in sequence.

```python
# B. Stocks (Portfolio Merge - Integer-based)
# ==========================================================
for firm_id, share in list(deceased.portfolio.holdings.items()):
    total_shares = share.quantity
    if total_shares <= 0 or not heirs:
        continue

    num_heirs = len(heirs)

    # 1. Calculate base shares and remainder
    shares_per_heir = total_shares // num_heirs
    remainder_shares = total_shares % num_heirs

    # 2. Distribute base shares to all heirs
    if shares_per_heir > 0:
        for heir in heirs:
            heir.portfolio.add(firm_id, shares_per_heir, share.acquisition_price)
            # Legacy Sync (assuming it remains necessary)
            current_legacy = heir.shares_owned.get(firm_id, 0.0)
            heir.shares_owned[firm_id] = current_legacy + shares_per_heir
            if simulation.stock_market:
                simulation.stock_market.update_shareholder(heir.id, firm_id, heir.shares_owned[firm_id])

    # 3. Distribute remainder shares one-by-one to heirs until exhausted
    for i in range(remainder_shares):
        heir = heirs[i]
        heir.portfolio.add(firm_id, 1, share.acquisition_price)
        # Legacy Sync
        current_legacy = heir.shares_owned.get(firm_id, 0.0)
        heir.shares_owned[firm_id] = current_legacy + 1
        if simulation.stock_market:
            simulation.stock_market.update_shareholder(heir.id, firm_id, heir.shares_owned[firm_id])

    # 4. Clear deceased's holding for this stock
    if simulation.stock_market:
        simulation.stock_market.update_shareholder(deceased.id, firm_id, 0)

# Clear entire portfolio at the end
deceased.portfolio.holdings.clear()
deceased.shares_owned.clear()
```

## 4. Implementation Plan
1.  **Target File**: `simulation/systems/inheritance_manager.py`
2.  **Target Method**: `process_death`
3.  **Action**:
    *   Locate the `Distribution (Transfer)` section (`# 5.`).
    *   Replace the cash distribution logic (approx. `L259-L278`) with the new integer-based pseudo-code from section 3.1.
    *   Replace the stock portfolio distribution logic (approx. `L280-L294`) with the new integer-based pseudo-code from section 3.2.
    *   **Crucially, remove the `remainder` block that transfers residual assets to the government.**

## 5. Verification & Test Plan
The implementation will be verified by updating existing tests and ensuring they pass with the new, correct logic.

### 5.1. Test Cases
-   **Test Case 1 (Even Split)**: 10,000 cash, 100 shares, 2 heirs. -> Each heir receives 5,000 cash and 50 shares exactly.
-   **Test Case 2 (Uneven Split)**: 10,000.01 cash, 101 shares, 2 heirs. -> Heir 1 receives 5000.00 cash and 50 shares. Heir 2 receives 5000.01 cash and 51 shares.
-   **Test Case 3 (Multiple Heirs)**: 100.00 cash, 10 shares, 3 heirs.
    -   Heir 1: 33.33 cash, 3 shares.
    -   Heir 2: 33.33 cash, 3 shares.
    -   Heir 3 (last): 33.34 cash, 4 shares.
-   **Test Case 4 (Zero Assets)**: 0 cash, 0 shares. -> No errors should occur.

### 5.2. Required Test Updates
-   **`tests/systems/test_inheritance_manager.py`**:
    -   Any test that asserts the government receives an `inheritance_residual` **must be updated or removed**.
    -   New assertions are required to verify that the *last heir* receives the rounding remainder for both cash and stocks.
    -   Assertions must confirm that `deceased.assets` is `0.0` after distribution.
-   **Fixtures**: Use existing fixtures from `tests/conftest.py` like `golden_households` to set up scenarios. No new fixtures should be required.

## 6. Risk & Impact Audit (Addressing Pre-flight Report)
This design explicitly acknowledges and mitigates the risks identified in the `TD-112 Pre-flight Audit Report`.

1.  **Architectural Constraint (God Object)**: **CONFIRMED**. The proposed solution continues to operate through the `simulation` object facade (`settlement.transfer`, `simulation.stock_market`, etc.). No new interfaces are introduced.
2.  **Architectural Constraint (Cash & Stocks)**: **CONFIRMED**. The pseudo-code provides distinct integer-based distribution logic for both cash (pennies) and stocks (indivisible units), satisfying the requirement.
3.  **Critical Risk (Logic Placement)**: **CONFIRMED**. The implementation plan clearly states that the changes occur in the final "Distribution" step of the `process_death` method, ensuring valuation, taxation, and liquidation have already completed.
4.  **Critical Risk (Test Failures)**: **CONFIRMED**. The `Verification & Test Plan` explicitly documents that tests validating the government's capture of `inheritance_residual` are now invalid. This is a required and intentional breaking change, and the tests must be updated to reflect the correct logic where the last heir receives the remainder.

## 7. Mandatory Reporting
As part of the implementation of this specification, the assigned developer (Jules) is required to:
1.  **Log Insights**: Document any non-obvious discoveries, edge cases, or emergent behaviors encountered during implementation in a new file under `communications/insights/`.
2.  **Record Technical Debt**: If any workarounds or sub-optimal patterns are required to complete the task, record them in `design/TECH_DEBT_LEDGER.md` with a reference to `TD-112`.
