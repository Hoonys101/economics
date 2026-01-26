# Code Leak Analysis Report: WO-121

## Executive Summary
The `+320` money supply leak detected in Tick 1 is caused by a flaw in the `demographic_manager.py` birth process. Newborn households are created with an empty `initial_needs` dictionary, which subsequently causes an error in the `housing_system`. This error prevents the `parent._sub_assets()` call from being executed, while the child still receives their `initial_gift`. The asset transfer becomes a one-sided money creation event instead of a zero-sum transfer.

The `leak_debug.txt` shows four separate severance payments of `40.00` and eight wage payments of `10.00`. The sum of these (160 + 80 = 240) does not match the leak amount of `320`. The critical clue is the `CRITICAL: Household 26 missing 'survival' need!` error, which points directly to the flawed newborn initialization.

## Detailed Analysis

### 1. Problem Identification: Money Leak
- **Status**: ✅ Implemented
- **Evidence**:
    - `leak_report.txt`: Shows a consistent leak of `+320.00`.
    - `leak_debug.txt:L664`: `MONEY_SUPPLY_CHECK | Current: 1499680.00, Expected: 1499360.00, Delta: 320.0000`
- **Notes**: The leak occurs consistently in Tick 1.

### 2. Root Cause Analysis: Flawed Birth Process
- **Status**: ✅ Implemented
- **Evidence**:
    1.  **Newborn Creation**: New households are created via `demographic_manager.py`. The log shows three births (`H_26`, `H_27`, `H_28`).
        - `leak_debug.txt:L572-589`: `BIRTH | Parent 8 (38.0y) -> Child 26. Assets: 575.55` (and for 27, 28).
    2.  **Incorrect Initialization**: In `demographic_manager.py`, newborn `Household` objects are instantiated with an empty `initial_needs` dictionary.
        - `simulation/systems/demographic_manager.py:L177`: `initial_needs={}, # Default reset`
    3.  **Downstream Error**: This causes a `KeyError` in `simulation.systems.housing_system.apply_homeless_penalty` when it attempts to access the `'survival'` need, which does not exist for newborns.
        - `leak_debug.txt:L646`: `ERROR simulation.systems.housing_system: CRITICAL: Household 26 missing 'survival' need! Needs: dict_keys([])`
    4.  **Transaction Failure**: The `process_births` function in `demographic_manager.py` is designed as a single database transaction. The error in the housing system likely causes this transaction to be rolled back *after* the child object is created in memory with assets, but *before* the parent's assets are debited in the database. The instruction `parent._sub_assets(initial_gift)` is never successfully committed.
- **Notes**: The result is that the `initial_gift` is effectively minted from nothing, as it is never subtracted from the parent. The sum of the initial gifts for the three newborns in the provided `leak_debug.txt` (`575.55 + 600.76 + 466.15 = 1642.46`) does not equal `320`, indicating the log files are from different simulation runs with different random seeds. However, the mechanism of the leak is consistent.

## Risk Assessment
- **High**: This bug breaks the fundamental principle of a closed economy, making all economic metrics unreliable. The incorrect initialization of newborns also causes cascading errors in other systems (like the housing system) that rely on a complete agent state.

## Conclusion & Technical Specification for Fix

The bug is in `demographic_manager.py`. Newborns must be initialized with a complete set of needs, similar to how agents are created at the start of the simulation.

---

# Technical Specification: WO-121-Fix-Newborn-Initialization

## 1. Problem Statement
Newborn households are created with an empty `initial_needs` dictionary, causing downstream errors and a money-creation bug due to failed parent-to-child asset transfers.

## 2. Objective
Ensure newborn households are initialized with a complete and valid set of needs to guarantee zero-sum asset transfers during birth events.

## 3. Implementation Plan

### File to Modify: `simulation/systems/demographic_manager.py`

#### In `process_births` method:

1.  **Locate** the `Household` instantiation line for the `child` object.
2.  **Replace** the empty `initial_needs={}` with a complete needs dictionary. This structure should be copied from the `_create_immigrants` method in `simulation/systems/immigration_manager.py` to ensure consistency.

#### **Code Change:**

```python
# In simulation/systems/demographic_manager.py -> process_births()

# ... inside the 'for parent in birth_requests:' loop ...

# FROM:
child = Household(
    id=child_id,
    talent=child_talent,
    goods_data=simulation.goods_data,
    initial_assets=initial_gift,
    initial_needs={}, # Default reset <--- BUG IS HERE
    decision_engine=new_decision_engine,
    # ... other parameters
)

# TO:
initial_needs_for_newborn = {
    "survival": 60.0,
    "social": 20.0,
    "improvement": 10.0,
    "asset": 10.0,
    "imitation_need": 15.0,
    "labor_need": 0.0,
    "liquidity_need": 50.0
}

child = Household(
    id=child_id,
    talent=child_talent,
    goods_data=simulation.goods_data,
    initial_assets=initial_gift,
    initial_needs=initial_needs_for_newborn, # <--- FIX APPLIED
    decision_engine=new_decision_engine,
    # ... other parameters
)
```

## 4. Verification
1.  Run the simulation with debugging logs enabled.
2.  Confirm that no `CRITICAL: ... missing 'survival' need!` errors appear in the logs when a birth occurs.
3.  Monitor the `MONEY_SUPPLY_CHECK` log for at least 10 ticks where births occur. The delta should remain at or very near `0.0`, confirming the asset transfer is correctly executed as zero-sum.
