# Spec: Track Alpha - Monetary Baseline & Leak Verification

## 1. Problem Statement
- **TD-115**: A monetary leak of **-99,680** is reported at Tick 1. The root cause is an incorrect calculation of the initial baseline money supply, which fails to account for all assets created during the simulation's bootstrapping phase.
- **TD-111**: The role of `EconomicRefluxSystem` in the money supply is ambiguous. It needs to be clarified whether it is part of the monetized economy or an off-books accounting tool.

This specification details a surgical fix to establish a correct, canonical M2 baseline at simulation start, thereby resolving both technical debts.

## 2. Root Cause Analysis (Based on Pre-flight Audit)
1.  **Incorrect Baseline Calculation**: `simulation/initialization/initializer.py` uses `sim.world_state.calculate_total_money()` to set the initial baseline. The audit reveals this method is flawed and does not represent the true total money supply (M2).
2.  **Conflicting Definitions**: The codebase contains multiple definitions of "money supply." The canonical and correct definition is found in `EconomicIndicatorTracker.get_m2_money_supply`, which correctly aggregates assets from households, firms, the bank, and the government. This is the **single source of truth**.
3.  **`RefluxSystem` Status**: The correct M2 calculation in `EconomicIndicatorTracker.get_m2_money_supply` already **intentionally and correctly excludes** the `EconomicRefluxSystem`'s balance, treating it as an off-books sink for verification purposes. The issue is not that the M2 function is wrong, but that the wrong function is being used for the initial baseline check.

The solution is to replace the incorrect function call in `initializer.py` with the correct, canonical M2 calculation method.

## 3. Proposed Solution
The fix is to replace the flawed baseline calculation at the end of `SimulationInitializer.build_simulation` with a call to the canonical `EconomicIndicatorTracker.get_m2_money_supply` method. This ensures the initial money supply is measured using the same logic that is used for subsequent leak-checking, guaranteeing a zero-sum start.

## 4. Interfaces (api.py)
No new interfaces are required. This fix leverages the existing, correct method signature:

- **File**: `simulation/metrics/economic_tracker.py`
- **Method**: `EconomicIndicatorTracker.get_m2_money_supply(self, world_state: 'WorldState') -> float`

## 5. Logic Flow / Implementation Steps

**File to Modify**: `simulation/initialization/initializer.py`

**Target Method**: `build_simulation(self) -> Simulation`

**Step-by-step Implementation**:

1.  Navigate to the end of the `build_simulation` method, just before the `return sim` statement.
2.  Locate the following line of code (`~L341`):
    ```python
    # TD-115: Establish baseline money supply AFTER all initialization steps
    sim.world_state.baseline_money_supply = sim.world_state.calculate_total_money()
    ```
3.  **Replace** this line with the corrected logic that calls the canonical M2 calculation method from the `EconomicIndicatorTracker`.

    **New Code:**
    ```python
    # TD-115 & TD-111 Fix: Establish baseline money supply using the canonical M2 definition
    # from the EconomicIndicatorTracker. This ensures the baseline is calculated with the
    # same logic used for subsequent leak verification.
    sim.world_state.baseline_money_supply = sim.tracker.get_m2_money_supply(sim.world_state)
    ```
4.  Ensure the surrounding logging statements are updated to reflect the corrected baseline calculation. The updated block should look like this:

    ```python
    # TD-115 & TD-111 Fix: Establish baseline money supply using the canonical M2 definition
    # from the EconomicIndicatorTracker. This ensures the baseline is calculated with the
    # same logic used for subsequent leak verification.
    sim.world_state.baseline_money_supply = sim.tracker.get_m2_money_supply(sim.world_state)
    self.logger.info(f"Initial baseline M2 money supply established: {sim.world_state.baseline_money_supply:,.2f}")

    return sim
    ```

## 6. Verification Plan
1.  **Initial Leak Check**: After applying the fix, run the simulation once. The initial money supply log should now report a much larger, more realistic number.
2.  **Run Leak Trace Script**: Execute `python scripts/trace_leak.py` (or equivalent) for the new run. The variance reported for Tick 1 should be `0.0` or extremely close to it, confirming TD-115 is resolved.
3.  **Full Test Suite Execution**: Run `pytest`. Expect several tests to fail.
4.  **Re-baseline Failing Tests**: The failing tests are expected, as they likely contain hardcoded assertions based on the old, incorrect baseline. Identify these tests and update their expected asset values to match the new, correct initial state.
5.  **Final Confirmation**: Once all tests pass, run the leak trace script one final time to provide formal proof of the fix for the pull request.

## 7. Risk & Impact Audit
- **Risk**: High probability of breaking existing unit and integration tests that rely on hardcoded initial financial state.
- **Mitigation**: The verification plan explicitly includes a step to identify, update, and re-baseline all affected tests. This is a necessary consequence of fixing a fundamental calculation error.
- **Architectural Impact**: This change is low-risk architecturally. It is a surgical, single-line fix that occurs at the very end of the high-risk initialization sequence, as recommended by the pre-flight audit. It reinforces the project's architectural pillar of "Single Source of Truth" by consolidating on a canonical M2 definition.

---
## 8. [Routine] Mandatory Reporting
Jules, during implementation, you are required to log any unexpected findings, side effects, or potential improvements. Create a new file in `communications/insights/` named `YYYY-MM-DD_track_alpha_findings.md` to document your observations. This is critical for continuous improvement and updating the `TECH_DEBT_LEDGER.md`.
