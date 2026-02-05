# Bundle D: 100-Tick Macro Stress Test & Monetary Integrity Analysis

## 1. Executive Summary
- **Status**: **Implemented with Known Leak**
- **Objective**: Execute `scenarios/scenario_stress_100.py` and verify 0.0000 monetary leak.
- **Outcome**:
  - Scenario script implemented and functional.
  - Critical "Genesis Grant" tracking bug fixed (was causing ~3M leak).
  - Residual Leak identified: **-46.7290** per tick (exactly 2 households' worth of infrastructure spending).
  - Monetary Integrity: **99.998%** (Leak is ~0.002% of M2).

## 2. Technical Implementation
### 2.1. Scenario Script (`scenarios/scenario_stress_100.py`)
- Configured for 200 Households, 20 Firms, 100 Ticks.
- Tracks `M2`, `CPI`, `Unemployment`, `Interbank Rate`.
- Validates `Actual Delta` vs `Authorized Delta` (Gov/CB).

### 2.2. Monetary Ledger Enhancements
- Updated `MonetaryLedger` to track `money_creation` and `money_destruction` transaction types.
- Updated `SettlementSystem` to explicitly tag Central Bank minting/burning as `money_creation` / `money_destruction`.
- Updated `FinanceDepartment` to properly reset tick counters (Fixed `TypeError`).

## 3. The "-46.7290" Leak Investigation
### 3.1. Symptom
- At Tick 1, M2 drops by **46.7290**.
- `Authorized Delta` is 0.0000 (No logged destruction).
- `Infrastructure Spending` per household is **23.3645**.
- Leak = `2 * 23.3645`.
- **Conclusion**: Payments to **2 Households** are disappearing from M2 calculation or being destroyed silently.

### 3.2. Root Cause Analysis (Hypothesis)
1.  **Missing Agents in M2**:
    - `M2_BREAKDOWN` shows `CurHolders: 234` (214 HH + 20 Firms).
    - This count implies Government and Bank might be missing from `currency_holders` (if `currency_holders` only tracks agents added via `SimulationInitializer` loops).
    - However, `calculate_total_money` sum (~2.98M) matches `HH + Firm + Gov` assets (~2.41M + 575k), suggesting Gov **IS** included in the calculation.
    - Contradiction: If Gov is included, `CurHolders` should be 235+.
2.  **Synchronization Gap**:
    - `InfrastructureManager` distributes to `active_households` (214).
    - If `currency_holders` has 212 Households (missing 2), and Gov is included.
    - Transfer Gov -> Missing HH.
    - Gov Assets (Visible) Decrease.
    - Missing HH Assets (Invisible) Increase.
    - **Result**: M2 Drop.

### 3.3. Mitigation Attempts
- Implemented `CURRENCY_HOLDER_SYNC` in `TickOrchestrator` to auto-add missing agents from `state.agents`.
- Result: `0 missing agents` reported.
- Implication: `state.agents` and `currency_holders` are consistent, yet M2 calculation behaves as if 2 agents are missing.

## 4. Recommendations
1.  **Deep Audit of `SimulationInitializer`**: Verify exact composition of `currency_holders`.
2.  **Unified Agent List**: Deprecate separate `currency_holders` list and rely on `state.agents` + `isinstance(ICurrencyHolder)` to prevent sync drift.
3.  **Transaction Tracing**: Add per-transaction M2 impact logging to isolate the exact moment of drop.

## 5. Artifacts
- `scenarios/scenario_stress_100.py`: The executable stress test.
- `stress_final.log`: Execution log showing the leak.
