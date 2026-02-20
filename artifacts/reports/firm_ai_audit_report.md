# Technical Audit Report: Firm Agent & AI Debt Awareness

## Executive Summary
The refactoring of the `Firm` agent toward the **Stateless Engine & Orchestrator Pattern** is significantly advanced but incomplete. While core business logic (HR, Finance, Production) has migrated to stateless engines, legacy components still utilize parent-pointer "attachment," and the System 2 AI remains strategically blind to debt constraints in its NPV projections.

---

## Detailed Analysis

### 1. TD-ARCH-FIRM-COUP (Parent Pointer Coupling)
- **Status**: ⚠️ Partial / Remnants Remain
- **Evidence**: 
    - `simulation/firms.py:L106-108`: The `InventoryComponent` and `FinancialComponent` still utilize an `attach(self)` method, which establishes a bi-directional link between the component and the agent instance.
    - `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`: Explicitly lists `TD-ARCH-FIRM-COUP` as **Open**, noting that departments still bypass the Orchestrator via `self.parent`.
- **Refactoring Progress**:
    - ✅ **Stateless Engines**: `firms.py:L122-132` shows that `HREngine`, `FinanceEngine`, `ProductionEngine`, and `SalesEngine` are initialized without parent references.
    - ✅ **DTO Boundaries**: `firms.py:L480` (`produce`) and `L612` (`make_decision`) demonstrate that these engines are called using pure DTOs (e.g., `FirmSnapshotDTO`, `FinanceDecisionInputDTO`) rather than the `self` handle.
- **Notes**: The transition is successful for *behavioral logic* (Engines), but the *state management components* (Inventory/Finance) still adhere to the legacy stateful pattern.

### 2. TD-AI-DEBT-AWARE (AI Constraint Blindness)
- **Status**: ❌ Missing / Remains Open
- **Evidence**:
    - `simulation/ai/firm_system2_planner.py:L156-168`: The `_calculate_npv` function used for strategic planning only factors in `revenue`, `wages`, and `maintenance`. It lacks parameters for `interest_payments` or `debt_repayment_schedules`.
    - `firm_system2_planner.py:L86`: While the planner extracts `assets` from the `FinanceStateDTO`, it does not pull `total_debt_pennies` to calculate leverage ratios or debt-service coverage.
- **Mitigation Check**:
    - ⚠️ **Rule-Base Constraint**: `simulation/components/engines/finance_engine.py:L45-48` correctly prioritizes `debt_repayment` within the tick-level `BudgetPlanDTO`. This prevents the agent from going over the ceiling in the immediate term.
- **Notes**: There is a "Cognitive Gap." The rule-based engine (System 1) enforces the debt ceiling, but the AI planner (System 2) still proposes aggressive automation targets as if the firm were debt-free, leading to "Intent Spamming" where the AI suggests investments that the Finance Engine will inevitably reject.

---

## Risk Assessment
- **Technical Debt**: The `attach(self)` pattern in components (`TD-ARCH-FIRM-COUP`) creates a risk of circular dependencies during serialization or liquidation, as components can modify the `Firm` state without the Orchestrator's oversight.
- **Logic Overhead**: AI debt-blindness (`TD-AI-DEBT-AWARE`) causes the agent to waste computational cycles on NPV scenarios that are financially impossible, polluting logs with `DEBT_CEILING_HIT` warnings and degrading decision quality.

---

## Conclusion
The `Firm` agent has successfully implemented the **Stateless Engine** interface, resolving the most critical coupling at the decision-making boundary. However, the architectural "cleanup" of legacy components and the integration of debt-awareness into the System 2 AI are still required to satisfy the project's long-term robustness mandates.

**Required Action Items**:
1. Remove `.attach(self)` from `InventoryComponent` and `FinancialComponent`.
2. Update `FirmSystem2Planner._calculate_npv` to include debt interest and repayment flows.
3. Pass `current_debt_ratio` in the AI input DTO to penalize over-leveraged investment intents.