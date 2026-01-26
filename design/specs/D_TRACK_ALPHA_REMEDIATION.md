# Spec: Track Alpha Remediation (TD-115 & TD-111)

## 1. Objectives

This document outlines the remediation plan for two critical monetary integrity issues:
1.  **TD-115 (CRITICAL):** Fix the source of a **-99,680 asset leak** that occurs at Tick 1, before any simulation steps are run. The investigation must focus on the agent/system initialization sequence.
2.  **TD-111 (ECONOMIC_RISK):** Correct the M2 money supply calculation to **exclude the `EconomicRefluxSystem` balance**, without breaking the system's zero-sum integrity checks.

## 2. 🚨 Risk & Impact Audit (Pre-flight Analysis)

This remediation is high-risk due to the following architectural constraints identified during the pre-flight audit.

-   **God Class Initializer**: `simulation/initialization/initializer.py:build_simulation` is a "God Method" that instantiates and wires the entire simulation. Changes to the initialization order are fragile and have a high risk of causing unforeseen side-effects.
-   **Conflicting Function Responsibility**: `world_state.py:calculate_total_money` serves two irreconcilable purposes:
    1.  **System Integrity Check**: A zero-sum validator ensuring no assets are created or destroyed.
    2.  **Economic Reporting**: An M2 money supply metric.
-   **Risk of Masking Leaks**: The fix for TD-111, if implemented incorrectly by modifying `calculate_total_money`, will break the system's primary leak detection tool. It would create constant false positives, masking the discovery of future, real asset leaks.

**Conclusion**: The implementation must strictly adhere to the plan below to avoid catastrophic architectural damage.

## 3. Remediation Plan: TD-115 (Tick 1 Asset Leak)

### 3.1. Hypothesis

The asset leak occurs because some components incur costs (`withdraw` is called) *before* all initial liquidity has been distributed and accounted for. Prime suspects are `Bootstrapper.force_assign_workers` and initial `agent.update_needs()` calls, which may trigger financial activity before the system's baseline money supply is established.

### 3.2. Investigation & Solution

#### Phase 1: Establish a Stable Baseline

The `WorldState` needs a definitive record of the total money that *should* exist at Tick 0.

1.  **Add Attribute to `WorldState`**: In `simulation/world_state.py`, add a new attribute to the `WorldState` class.

    ```python
    # simulation/world_state.py

    class WorldState:
        def __init__(...):
            # ... existing attributes
            self.baseline_money_supply: float = 0.0
            # ...
    ```

2.  **Set Baseline in `SimulationInitializer`**: In `simulation/initialization/initializer.py`, after all agents and liquidity have been created, calculate the total money supply *once* and set it as the baseline.

    ```python
    # simulation/initialization/initializer.py

    class SimulationInitializer:
        def build_simulation(self) -> Simulation:
            # ... (all initialization logic from sim.settlement_system = ... to Bootstrapper.force_assign_workers(...))

            # NEW: After all agents and initial funds are created
            sim.world_state.baseline_money_supply = sim.world_state.calculate_total_money()
            self.logger.info(f"Initial baseline money supply established: {sim.world_state.baseline_money_supply:,.2f}")

            # ... (rest of initialization)
            return sim
    ```

    *Note: This change will likely reveal that `calculate_total_money()` already returns the incorrect value at this stage. The next step is to find out why.*

#### Phase 2: Pinpoint the Leak

The order of operations in `build_simulation` is flawed. The `Bootstrapper` calls are the most likely source of the leak.

1.  **Re-order `Bootstrapper` Calls**: In `initializer.py`, ensure that liquidity is injected *before* workers are assigned. Worker assignment may trigger costs (e.g., signing bonuses, administrative fees) that cause the leak if firms have no cash.

    ```python
    # simulation/initialization/initializer.py

    # Correct Order:
    # 1. Inject money first.
    Bootstrapper.inject_initial_liquidity(sim.firms, self.config)
    # 2. Then assign workers, which might have associated costs.
    Bootstrapper.force_assign_workers(sim.firms, sim.households)
    ```

2.  **Verify**: After re-ordering, run the simulation. The leak should be resolved. The value logged for `baseline_money_supply` should now be positive and match the expected total initial assets.

## 4. Remediation Plan: TD-111 (Reflux M2 Calculation)

### 4.1. Mandate

**DO NOT MODIFY `world_state.py:calculate_total_money`.** This function must be preserved as the system's zero-sum integrity check.

### 4.2. Solution

Create a new, dedicated method for economic reporting within the `EconomicIndicatorTracker`.

1.  **Create New Method**: In `simulation/metrics/economic_tracker.py`, add a new method `get_m2_money_supply`.

    ```python
    # simulation/metrics/economic_tracker.py
    from __future__ import annotations
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from simulation.world_state import WorldState

    class EconomicIndicatorTracker:
        # ... existing methods

        def get_m2_money_supply(self, world_state: 'WorldState') -> float:
            """
            Calculates the M2 money supply for economic reporting.
            M2 = Household_Assets + Firm_Assets + Bank_Reserves + Government_Assets
            This calculation EXCLUDES the RefluxSystem balance, as it represents
            money in transit not yet realized by economic agents.
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

            return total
    ```

2.  **Update Consumers**: Any part of the codebase that requires the M2 money supply for reporting (e.g., `generate_phase1_report.py`, `dashboard/app.py`) must be updated to call `tracker.get_m2_money_supply(world_state)` instead of `world_state.calculate_total_money()`.

## 5. API & Interface Changes

-   **`simulation.world_state.WorldState`**:
    -   ADD: `baseline_money_supply: float = 0.0`
-   **`simulation.metrics.economic_tracker.EconomicIndicatorTracker`**:
    -   ADD: `get_m2_money_supply(self, world_state: 'WorldState') -> float`

## 6. Verification Plan

1.  **TD-115 Verification**:
    -   Start a new simulation.
    -   At Tick 0, check the logs for the `Initial baseline money supply established` message.
    -   Assert that the logged value equals the sum of all configured initial assets (e.g., `config.INITIAL_BANK_ASSETS` + `config.INITIAL_FIRM_LIQUIDITY` * num_firms). The value should be positive and correct.
    -   Run the simulation for 1 tick. Verify no new leaks are reported by the zero-sum check.

2.  **TD-111 Verification**:
    -   Run a simulation for ~10 ticks until `reflux_system.balance` is greater than 0.
    -   Pause the simulation.
    -   Invoke `ws_total = world_state.calculate_total_money()`.
    -   Invoke `m2_total = tracker.get_m2_money_supply(world_state)`.
    -   Invoke `reflux_balance = world_state.reflux_system.balance`.
    -   Assert `abs(ws_total - (m2_total + reflux_balance)) < 1e-6`. The zero-sum total must equal the M2 total plus the reflux balance.

---

## 7. [Routine] Mandatory Reporting

-   Upon completion, document any new insights or discovered technical debt in `communications/insights/`.
-   Update the `TECH_DEBT_LEDGER.md` with the status of **TD-115** and **TD-111** to `RESOLVED`.
