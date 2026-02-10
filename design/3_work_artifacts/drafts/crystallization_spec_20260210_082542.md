# Crystallization Spec: 2026-02-10

## 📂 1. Archive Operations
Move the following files to `design/_archive/insights/`:
- `design/3_work_artifacts/reports/inbound/fix-sales-tax-atomicity-inheritance-audit-643742581835242417_FIRM-RESET-FIX.md` -> `2026-02-10_Tick_Level_State_Reset_Integrity.md`

## 🏛️ 2. Economic Insights Entry
Add to `design/2_operations/ledgers/ECONOMIC_INSIGHTS.md` under `[System] Architecture & Infrastructure`:
- **[2026-02-10] Tick-Level State Reset Integrity**
    - **Principle**: To ensure data availability for all simulation phases (e.g., learning, analysis), agent state variables relevant for an entire tick (`expenses_this_tick`) must only be reset at the very end of the simulation cycle (i.e., in the Post-Sequence phase). Resetting state mid-cycle leads to data loss for later-stage processes.
    - **Implementation**: Enforce a standardized `reset()` method on agents, to be called exclusively by the orchestrator during the final phase of a tick.
    - [Insight Report](../_archive/insights/2026-02-10_Tick_Level_State_Reset_Integrity.md)

## 🔴 3. Technical Debt Synchronization
Register new debt in `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`:
- **[TD-FIRM-GOD-OBJECT] [Open] The `Firm` class is a "God Object" with legacy proxy properties.**
    - **Description**: The `Firm` class combines multiple concerns (finance, production, etc.) and uses legacy patterns like the `finance` property returning `self` for backward compatibility. This creates fragile, non-obvious dependencies in orchestration code and increases the risk of state management errors.
    - **Impact**: High. Obscures true component structure, complicates maintenance, and violates Separation of Concerns.
    - **Source**: [Insight Report](../_archive/insights/2026-02-10_Tick_Level_State_Reset_Integrity.md)
