# Specification: PH6_STRESS_TEST

## 1. Overview

**Purpose**: This document specifies the design and pass/fail criteria for the "100-Tick Stress Test". The primary objective is to validate the monetary integrity (v1.0.0 "Closed-Loop Economy") of the simulation under a significantly higher agent load than standard runs.

**Scope**: This test serves as the entry gate for Phase 6, ensuring the architectural stability and performance of the core engine before introducing new market dynamics. It focuses on verifying the absence of money leaks and monitoring key macroeconomic indicators for signs of instability.

---

## 2. Test Parameters

The simulation will be initialized with the following configuration overrides:

| Parameter | Value | Rationale |
|:----------|:------|:----------|
| `NUM_HOUSEHOLDS` | 200 | 10x the standard load to stress test agent processing. |
| `NUM_FIRMS` | 20 | 5x the standard load to increase market complexity. |
| `SIMULATION_TICKS` | 100 | Sufficient duration to observe emergent macro trends and instabilities. |
| `GOLD_STANDARD_MODE`| `False` | Enables credit creation, a primary vector for potential money leaks. |
| `RANDOM_SEED` | 42 | Ensures reproducibility of the test run. |
| `BATCH_SAVE_INTERVAL`| 100 | Disable frequent DB writes to isolate in-memory performance. |
| **Banks** | 1 | **Note:** The current architecture supports one commercial Bank. The test will proceed with N=1. Expansion to N>1 banks is a future goal. |

---

## 3. Execution Logic

The test will be executed via a headless Python script (`scenarios/scenario_stress_100.py`).

1.  **Initialization**: The script will invoke `utils.simulation_builder.create_simulation` with the parameters defined above.
2.  **Tick Loop**: The script will iterate for `SIMULATION_TICKS`. In each tick:
    a. `simulation.run_tick()` is called.
    b. **Monetary Integrity Check**: After the tick, the script will perform a money supply verification identical to the one in `TickOrchestrator._finalize_tick`:
        i. `current_money` is calculated via `world_state.calculate_total_money()`.
        ii. `expected_money` is calculated as `world_state.baseline_money_supply + world_state.government.get_monetary_delta()`.
        iii. `delta = current_money - expected_money`.
        iv. An assertion, `assert abs(delta) < 1.0`, will immediately halt the test on failure.
    c. **Data Logging**: Key macroeconomic indicators will be logged at each tick for post-run analysis.
3.  **Finalization**: After 100 ticks, a "Final Health Report" will be printed to the console, summarizing the end-state of the simulation.

---

## 4. Pass/Fail Criteria

| Type | Criteria | Details |
|:-----|:---------|:--------|
| **Primary (FAIL)** | **`abs(delta) >= 1.0`** | **Any money leak is a critical failure.** The test will halt immediately. |
| Secondary (WARN) | Simulation Time > 15 minutes | Indicates a significant performance bottleneck under load. |
| Secondary (WARN) | Hyperinflation / Deflation | Sustained CPI change > 5% per tick suggests model instability. |
| Secondary (WARN) | Market Collapse | Unemployment rate reaching 100% or 0%, or Interbank Call Rate becoming zero/NaN. |

---

## 5. Monitored Metrics

The following metrics will be tracked and included in the final report:

- **Monetary Delta**: The per-tick money supply leakage.
- **Cumulative CPI**: The consumer price index, tracked over time.
- **Unemployment Rate**: The percentage of the workforce unemployed.
- **Interbank Call Rate**: The interest rate for overnight lending between banks.
- **GDP**: Gross Domestic Product.
- **Population**: Total number of active households.

---

## 6. Risk & Impact Audit (Pre-flight Analysis)

This test is designed to probe the architectural risks identified in the pre-flight audit.

-   **`WorldState` God Class**: The test script will operate only through the `Simulation` facade, respecting the DTO-based state transition protocol. Success validates the robustness of the `_drain_and_sync_state` pattern under load.
-   **`currency_holders` Registration**: **CRITICAL DEPENDENCY.** The test's success hinges on the `SimulationInitializer` correctly appending all Households, Firms, the Bank, and Central Bank to the `world_state.currency_holders` list. A failure here guarantees a test failure.
-   **Genesis Protocol Integrity**: The per-tick assertion directly validates the atomic perfection of the initial money distribution. Any initial imbalance will cascade and be caught on Tick 1.
-   **Sequential Phasing Performance**: Running with 200+ agents will immediately expose any `O(n^2)` or higher complexity algorithms in the phasing loop, providing a clear benchmark for required optimizations.
-   **Monetary Actor Assumptions**: The test re-activates the Interbank market. The monetary verification logic assumes only the Government creates/destroys money. This test will correctly fail if the Interbank implementation violates this assumption, proving the robustness of the check.
