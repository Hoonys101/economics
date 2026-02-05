# Mission Guide: 100-Tick Macro Stress Test [Bundle D]

This document provides the blueprint for implementing and executing the Phase 6 Stress Test.

## 1. Objectives
- Implement `scenarios/scenario_stress_100.py`.
- Verify **Monetary Integrity (v1.0.0)** under 10x Household load (200 agents).
- Monitor Inflation and Liquidity indicators over 100 ticks.

## 2. Reference Context (MUST READ)
- **Design Spec**: [PH6_STRESS_TEST_SPEC](file:///c:/coding/economics/design/3_work_artifacts/drafts/draft_101313_Goal_Create_a_robust_100tick.md)
- **Baseline Logic**: [TickOrchestrator._finalize_tick](file:///c:/coding/economics/simulation/orchestration/tick_orchestrator.py#L191-L206) (Monetary verification logic)

## 3. Implementation Roadmap

### Phase 1: Scenario Script Creation
- Create `scenarios/scenario_stress_100.py`.
- Use `utils.simulation_builder.create_simulation` with the following overrides:
  - `NUM_HOUSEHOLDS: 200`
  - `NUM_FIRMS: 20`
  - `GOLD_STANDARD_MODE: False` (Credit creation enabled)
  - `SIMULATION_TICKS: 100`

### Phase 2: Per-Tick Assertion Loop
- In each tick:
  1. `sim.run_tick()`
  2. Calculate `current_money` vs `expected_money` (baseline + gov_delta).
  3. **CRITICAL**: `assert abs(delta) < 1.0`. (0.0000 is the target).
  4. Log: Tick, CPI, Unemployment, Interbank Rate, M2 Delta.

### Phase 3: Reports & Logging
- Print a **Final Health Report** at Tick 100 including:
  - Total GDP growth.
  - Average Inflation rate.
  - Final M2 Integrity status.

## 4. Verification
- **Primary**: Simulation completes 100 ticks without assertion failure.
- **Secondary**: `trace_leak.py` run at the end must show 0.0000.
- **Observation**: Note any "Inflation Drift" or "Liquidity Traps" in the logs.
