# Work Order: TRACK_ALPHA_SPEC - Monetary Initialization & Leak Hunt

**Phase:** 3
**Priority:** HIGH
**Prerequisite:** None

## 1. Problem Statement & Objectives

The simulation is experiencing two critical monetary leaks (TD-111, TD-115), which violate the core "Zero-Sum Financial Integrity" principle.
- **TD-115:** A consistent monetary leak of **-99,680** is reported at Tick 1, indicating an incomplete accounting of assets during the initial baseline measurement.
- **TD-111:** Intermittent M2 money supply fluctuations are observed during the simulation run, falsely reporting leaks. This is caused by inconsistent measurement timing relative to the operations of the `EconomicRefluxSystem`.

**Objective:**
Ensure Zero-Sum financial integrity by correcting the initial baseline calculation and standardizing the M2 money supply measurement process across the entire simulation lifecycle.

## 2. Root Cause Analysis (Summary of Audit)

- **TD-115 (Initial Leak):** The function used to set the initial money supply baseline (`world_state.calculate_total_money()`) fails to account for the balance of all `IFinancialEntity` instances created during initialization. The `EconomicRefluxSystem` is a prime candidate for this uncounted entity, as it exists outside the standard agent lists (households, firms, government).
- **TD-111 (Timing Leak):** The `EconomicRefluxSystem` violates the "Sacred Sequence" protocol by directly modifying agent assets outside the formal Transaction Phase. It captures money, temporarily holding it as a sink, and redistributes it later. M2 measurements taken between capture and distribution will incorrectly report a leak. The problem is not the M2 formula itself, but the lack of a canonical, enforced measurement point in the simulation loop.

## 3. Implementation Plan

This plan addresses both technical debts by centralizing the M2 calculation logic and enforcing a strict measurement protocol.

### Track A: Fix for TD-115 (Initial Baseline Leak)

**Goal:** Modify the M2 calculation to be comprehensive, accounting for all financial entities, including the `EconomicRefluxSystem`. This new function will be used to establish a correct initial baseline.

1.  **Centralize M2 Calculation in `EconomicIndicatorTracker`:**
    - In `simulation/metrics/economic_tracker.py`, the existing `get_m2_money_supply` method will be refactored and renamed to `calculate_m2`.
    - This method will be made a `@staticmethod` to be universally accessible.
    - It will accept the `world_state` and a new boolean flag `include_reflux_balance` to explicitly control whether the `EconomicRefluxSystem`'s balance is included in the total.

2.  **Update `SimulationInitializer` to Use New Method for Baseline:**
    - In `simulation/initialization/initializer.py`, locate the line where the baseline money supply is set:
      ```python
      # TD-115: Establish baseline money supply AFTER all initialization steps
      sim.world_state.baseline_money_supply = sim.world_state.calculate_total_money()
      ```
    - Replace this call with the new, centralized method from the `EconomicIndicatorTracker`:
      ```python
      # TD-115: Establish a comprehensive baseline money supply AFTER all initialization steps
      # The initial baseline MUST include the reflux system's balance (which should be 0, but is included for correctness).
      from simulation.metrics.economic_tracker import EconomicIndicatorTracker
      sim.world_state.baseline_money_supply = EconomicIndicatorTracker.calculate_m2(
          sim.world_state, include_reflux_balance=True
      )
      ```

### Track B: Fix for TD-111 (M2 Measurement Timing)

**Goal:** Enforce a strict, non-negotiable point in the simulation loop for all official M2 measurements to occur, neutralizing the timing issue caused by the `EconomicRefluxSystem`.

1.  **Define Canonical Measurement Point:**
    - The official M2 money supply for any given tick **must** be measured at the **end of Phase 4 (Lifecycle)**, *after* the `EconomicRefluxSystem.distribute()` method has completed.
    - This ensures that all money held temporarily by the reflux system has been returned to the economy before the final balance is taken.

2.  **Relocate `EconomicIndicatorTracker.track()` Call:**
    - The call to `sim.tracker.track()` within the main simulation loop (`TickScheduler`) must be moved to this new canonical point at the end of Phase 4.
    - When `track()` is called, it will internally use the new `calculate_m2` static method with the flag `include_reflux_balance=False`, as the reflux balance is correctly considered "in-flight" during the tick.

3.  **Update All Verification Scripts:**
    - All diagnostic and verification scripts (e.g., `scripts/diagnose_money_leak.py`, `scripts/audit_zero_sum.py`) that perform money supply calculations must be updated to use the new canonical method:
      `EconomicIndicatorTracker.calculate_m2(world_state, include_reflux_balance=False)`
    - This ensures that debugging tools and official metrics use the exact same logic.

## 4. API & Interface Definitions

The following changes will be made to `simulation/metrics/economic_tracker.py`.

```python
# simulation/metrics/economic_tracker.py

from __future__ import annotations
from typing import List, Dict, Any, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from simulation.world_state import WorldState

# ... existing class ...

class EconomicIndicatorTracker:
    # ... existing __init__ and other methods ...

    def track(
        self,
        time: int,
        world_state: 'WorldState'
    ) -> None:
        """
        Calculates and records economic indicators for the current tick using the world_state.
        This method should be called at the canonical measurement point (end of Phase 4).
        """
        # ... existing tracking logic using world_state ...
        
        # M2 is now calculated using the canonical static method.
        # Reflux balance is EXCLUDED for in-tick tracking.
        m2_supply = EconomicIndicatorTracker.calculate_m2(world_state, include_reflux_balance=False)
        record["money_supply"] = m2_supply

        # ... rest of the tracking logic ...

    # DEPRECATE the old get_m2_money_supply in favor of the static method
    # def get_m2_money_supply(self, world_state: 'WorldState') -> float:
    #     ...

    @staticmethod
    def calculate_m2(world_state: 'WorldState', include_reflux_balance: bool = False) -> float:
        """
        Calculates the canonical M2 money supply for the simulation.

        M2 = Household_Assets + Firm_Assets + Bank_Reserves + Government_Assets
             [+ RefluxSystem_Balance if include_reflux_balance is True]

        Args:
            world_state: The current state of the simulation.
            include_reflux_balance: If True, includes the balance of the EconomicRefluxSystem.
                                    This should only be True for the initial baseline measurement.
        Returns:
            The total M2 money supply.
        """
        total = 0.0

        # 1. Households
        for h in world_state.households:
            if getattr(h, "is_active", True):
                total += h.assets

        # 2. Firms
        for f in world_state.firms:
            if getattr(f, "is_active", False):
                total += f.assets

        # 3. Bank Reserves
        if world_state.bank:
            total += world_state.bank.assets

        # 4. Government Assets
        if world_state.government:
            total += world_state.government.assets

        # 5. [Optional] Reflux System Balance
        if include_reflux_balance and world_state.reflux_system:
            total += world_state.reflux_system.balance

        return total
```

## 5. Verification Plan

1.  **TD-115 Verification:**
    - **Unit Test:** Create a test for `EconomicIndicatorTracker.calculate_m2` that constructs a mock `world_state` containing a `reflux_system` with a non-zero balance.
      - Assert that `calculate_m2(ws, include_reflux_balance=True)` returns the sum including the reflux balance.
      - Assert that `calculate_m2(ws, include_reflux_balance=False)` returns the sum excluding the reflux balance.
    - **Integration Test:** After applying the fix in `SimulationInitializer`, run the simulation. Check the logs for the `run_id` and verify that the initial `baseline_money_supply` is now correct and the leak report for Tick 1 is `0.0`.

2.  **TD-111 Verification:**
    - **Code Review:** Confirm that the `tracker.track()` call has been moved to the end of Phase 4 in the main simulation loop.
    - **Integration Test:** Run the `diagnose_money_leak.py` script over a 200-tick simulation run. The script should report no M2 variance from tick to tick, confirming that the measurement timing is now consistent.

## 6. Risk & Impact Audit

- **High Impact / Medium Risk**: This change modifies a fundamental aspect of the simulation's economic accounting.
  - **Impact:** `SimulationInitializer`, `EconomicIndicatorTracker`, and the main `TickScheduler` will be modified. All scripts and components that measure money supply must be updated.
  - **Risk of Regression:** Metrics that depend on M2 (e.g., Velocity of Money) will be affected. Their calculations must be reviewed to ensure they still produce correct results after the change. By centralizing the M2 calculation, this risk is mitigated, but manual verification is still required.
  - **Risk of Incomplete Update:** A developer might miss updating an auxiliary script that calculates money supply independently. A project-wide search for "assets" and "balance" summation loops is recommended to find and replace all instances with the new canonical method.
