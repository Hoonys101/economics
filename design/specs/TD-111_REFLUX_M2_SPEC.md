# Spec: TD-111 (Reflux M2 Calculation)

## 1. Objectives

This document provides the detailed technical specification for remediating **TD-111 (ECONOMIC_RISK)**. The goal is to create an accurate M2 money supply metric for economic reporting that correctly excludes funds in transit within the `EconomicRefluxSystem`.

This will be achieved by creating a new, dedicated function for M2 calculation, while preserving the existing `WorldState.calculate_total_money` method as a critical zero-sum system integrity check.

## 2. 🚨 Risk & Impact Audit (Pre-flight Analysis)

The implementation must mitigate the following critical risks identified during the pre-flight audit:

-   **Conflicting Function Responsibility (CRITICAL):** The function `simulation.world_state.py:calculate_total_money` serves a dual purpose: a zero-sum asset integrity check and an economic metric. Its primary, non-negotiable role is the integrity check. **This function must not be modified.**
-   **Risk of Masking Asset Leaks:** Any change to `calculate_total_money` (e.g., by excluding the reflux balance) will break the system's only reliable leak detection mechanism. It would create constant false positives, masking future, real asset leaks.
-   **Circular Dependency:** `WorldState` and `EconomicIndicatorTracker` have a mutual dependency. The implementation must preserve the existing `typing.TYPE_CHECKING` block to prevent a `CircularImport` error at runtime.
-   **Implicit API Contract Breach:** Failure to update all downstream consumers (reporting scripts, dashboards) to use the new M2 calculation method will result in continued, silent use of the incorrect metric.

## 3. Implementation Plan

### 3.1. Task: Create Dedicated M2 Money Supply Method

A new method, `get_m2_money_supply`, will be implemented in the `EconomicIndicatorTracker` class. This method will be solely responsible for calculating the M2 money supply for economic reporting.

1.  **Modify `economic_tracker.py`**: Add the following method to the `EconomicIndicatorTracker` class in `simulation/metrics/economic_tracker.py`.

    ```python
    # simulation/metrics/economic_tracker.py
    from __future__ import annotations
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from simulation.world_state import WorldState
    
    class EconomicIndicatorTracker:
        # ... existing methods ...

        def get_m2_money_supply(self, world_state: 'WorldState') -> float:
            """
            Calculates the M2 money supply for economic reporting.
            
            M2 = Household_Assets + Firm_Assets + Bank_Reserves + Government_Assets
            
            This calculation INTENTIONALLY EXCLUDES the EconomicRefluxSystem balance, 
            as it represents money in transit not yet realized by economic agents,
            and also excludes the Central Bank's balance which is used for
            system-level integrity checks.
            """
            total = 0.0

            # 1. Households
            for h in world_state.households:
                if h.is_active:
                    total += h.assets

            # 2. Firms
            for f in world_state.firms:
                if f.is_active:
                    total += f.assets

            # 3. Bank Reserves
            if world_state.bank:
                total += world_state.bank.assets

            # 4. Government Assets
            if world_state.government:
                total += world_state.government.assets

            # NOTE: world_state.reflux_system.balance is INTENTIONALLY EXCLUDED.
            # NOTE: world_state.central_bank.assets is INTENTIONALLY EXCLUDED.

            return total
    ```

### 3.2. Task: Audit and Update Consumers

Identify all codebase locations that currently use `world_state.calculate_total_money()` for economic reporting and update them to use the new `tracker.get_m2_money_supply(world_state)` method.

**Known Consumers (Incomplete List):**
-   `scripts/generate_phase1_report.py`
-   `scripts/analyze_history.py`
-   `dashboard/app.py`
-   Any Jupyter notebooks or analysis scripts that load and inspect `WorldState`.

A full codebase search for `calculate_total_money` must be performed to ensure all instances are updated.

## 4. API & Interface Changes

-   **`simulation.metrics.economic_tracker.EconomicIndicatorTracker`**:
    -   **ADD**: `get_m2_money_supply(self, world_state: 'WorldState') -> float`

## 5. Verification Plan

The fix will be verified by ensuring the zero-sum integrity check remains valid while the new M2 metric provides the correct, smaller value.

1.  **Run Simulation**: Execute a simulation for at least 10 ticks, or until the `reflux_system.balance` is confirmed to be greater than 0.
2.  **Pause and Inspect**: Pause the simulation and obtain the following values:
    -   `ws_total = world_state.calculate_total_money()`
    -   `m2_total = world_state.tracker.get_m2_money_supply(world_state)`
    -   `reflux_balance = world_state.reflux_system.balance`
    -   `cb_balance = world_state.central_bank.assets.get('cash', 0.0)`
3.  **Assert Correctness**: The following condition must be true, confirming that the total system money (for integrity checks) is the sum of the M2 supply (for reporting) and the money currently in transit or held by the central bank.

    ```python
    # Verification assertion
    assert abs(ws_total - (m2_total + reflux_balance + cb_balance)) < 1e-6
    ```

## 6. [Routine] Mandatory Reporting

-   Upon completion, document any new insights or discovered technical debt in `communications/insights/`.
-   Update the `design/TECH_DEBT_LEDGER.md` file, changing the status of **TD-111** to `RESOLVED`.
