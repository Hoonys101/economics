# 🏦 Phase 28: Structural Stabilization & Debt Repayment Plan (v2)

**Subject:** "Operation Abstraction Wall" & Final Purity Cleanup
**Date:** 2026-01-28
**Goal:** Liquidate structural risks from the Phase 23 "Industrial Revolution" expansion and enforce total architectural purity.

---

## 1. Status Analysis

The "Sacred Refactoring" and "Phase 23 Reactivation" have introduced high-impact features (Scenario System, Order-Book driven consumption), but at the cost of some technical debt.

### 🔴 Immediate Structural Risks
- **TD-103**: DecisionContext passes DTOs but isn't strictly enforced/vetted across all agents.
- **TD-132**: Hardcoded `GOVERNMENT_ID = 25`.
- **TD-133**: Scenarios directly mutate global `config` via `setattr`.
- **TD-134**: Market logic branches on `is_phase23` flags instead of generic strategies.

---

## 2. Repayment Tracks

### 🛤️ Track X: The Abstraction Wall (TD-103)
- **Objective**: Total decoupling of Agents from World Objects.
- **Action**:
    - Audit `DecisionContext` construction.
    - Ensure `goods_data` and `market_data` are converted to immutable TypedDicts/DTOs.
    - Implement a decorator-based `PurityGate` that blocks live object access during decision phase.

### 🛤️ Track Y: Infrastructure Dynamics (TD-132, TD-133)
- **Objective**: Remove hardcoded dependencies and namespace config.
- **Action**:
    - Refactor `SimulationInitializer` to search for `Government` agent by type rather than ID.
    - Move scenario parameter injection into a dedicated `config.scenario` dictionary.

### 🛤️ Track Z: Strategy Generalization (TD-134)
- **Objective**: Formalize the "Phase 23" logic into generic market behaviors.
- **Action**:
    - Replace `if is_phase23:` with `if market.model == "DIRECT_CONSUMPTION":`.
    - This allows future "Great Depression" or "Socialist" scenarios to use the same toggleable mechanisms.

---

## 3. Execution Sequence

1.  **Merge Phase 23 (WO-053)**: Force merge despite minor debts to unblock the main track.
2.  **Assign WO-135 (TD-103)**: Handled by Architect (Antigravity) + Gemini for spec, Jules for code.
3.  **Assign WO-136 (TD-133/134)**: Clean up the configuration and branching mess.
4.  **Assign WO-137 (TD-122)**: Final reorganization of the `tests/` directory (Cleanroom).

---
> [!NOTE]
> As the Team Leader, I authorize the immediate merge of the current expansion branch. The identified debts (TD-132~134) are manageable and will be prioritized in the upcoming cleanup session.
