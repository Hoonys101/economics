# AUDIT_REPORT_STRUCTURAL

**Generated Date**: 2024-05-22
**Auditor**: Jules
**Scope**: Structural Integrity Scan per `AUDIT_SPEC_STRUCTURAL.md`

## 1. Executive Summary

This audit evaluates the codebase against the 'DTO Decoupling' and 'Component SoC' architectural standards. The scan identified **2 God Classes** exceeding size limits and **2 significant module dependency violations**. While strict "Leaky Abstraction" via `DecisionContext` appears controlled, the reliance on legacy state dictionaries persists. The "Sacred Sequence" is mostly respected, with a notable exception regarding `Bankruptcy` phase ordering.

## 2. God Class Detection

The following classes exceed the 800-line threshold or mix >3 domain responsibilities:

| Class Name | File Path | Lines of Code | Responsibilities Identified |
| :--- | :--- | :--- | :--- |
| **Firm** | `simulation/firms.py` | 1742 | Production, Sales, HR, Finance, Asset Management (All-in-one) |
| **Household** | `simulation/core_agents.py` | 1166 | Consumption, Labor, Investment, Social, Biological Needs |

**Recommendation**: Immediate decomposition of `Firm` and `Household` into smaller, focused components is required to improve maintainability and testability.

## 3. Leaky Abstraction Analysis

### `DecisionContext` Purity
*   **Status**: **PASS (with caveats)**
*   **Findings**:
    *   Direct passing of `self` (Agent instance) to `DecisionContext` was **not found** in automated scans.
    *   Both `Household` and `Firm` utilize `create_state_dto()` or `get_snapshot_dto()` to populate context.
    *   **Caveat**: `HouseholdStateDTO` still relies on `agent_data` (a raw dictionary) for some internal state transfer, which is a "soft leak" of internal structure, though not the object reference itself.

### `make_decision` Interface
*   **Status**: **PASS**
*   **Findings**:
    *   Arguments are strictly typed DTOs (`DecisionInputDTO`).
    *   Return values are strictly typed (`List[Order]`, metadata).

## 4. Module Dependency & SoC (Separation of Concerns)

The audit traced `import` statements to identify layer violations.

### Critical Violations (Circular Dependency / Layer Inversion)
*   **Violation 1**: `modules/household/services.py` imports `Household` from `simulation.core_agents`.
    *   *Impact*: Low-level module depends on high-level orchestration agent.
*   **Violation 2**: `modules/firm/orchestrators/firm_action_executor.py` imports `Firm` from `simulation.firms`.
    *   *Impact*: Execution logic is coupled to the specific `Firm` implementation, preventing polymorphic behavior or easier testing.

### Utility Status
*   `simulation/utils/config_factory.py`: **CLEAN** (No domain coupling).
*   `simulation/utils/golden_loader.py`: **CLEAN** (Infrastructure only).

## 5. Sacred Sequence Verification

**Spec Requirement**: `Decisions -> Matching -> Transactions -> Lifecycle`

**Observed Sequence (`TickOrchestrator`)**:
1.  `Phase1_Decision` (**Decisions**)
2.  `Phase_Bankruptcy` (**Lifecycle/System** - *Early Execution*)
3.  `Phase_HousingSaga`
4.  `Phase_SystemicLiquidation`
5.  `Phase_Politics`
6.  `Phase2_Matching` (**Matching**)
7.  `Phase3_Transaction` (**Transactions**)
8.  `Phase_Consumption` (**Lifecycle**)
9.  `Phase5_PostSequence` (**Lifecycle**)

**Analysis**:
*   The core sequence `Decisions -> Matching -> Transactions` is respected.
*   **Deviation**: `Bankruptcy` runs *before* `Matching`. This is a significant deviation from "Lifecycle last". However, logically, bankrupt firms should be removed before matching to prevent invalid trades.
*   **Conclusion**: The sequence is functionally sound but strictly violates the "Lifecycle Last" dictate for the specific case of Bankruptcy. This should be documented as an intentional deviation or refactored if strict adherence is required.

## 6. Action Items

1.  **Refactor God Classes**: Prioritize `Firm` decomposition. Move logic to `modules/firm/` components.
2.  **Fix Module Dependencies**: Remove `from simulation.firms import Firm` in `modules/firm/`. Use `IFirm` protocol or dependency injection.
3.  **Harden DTOs**: Replace `agent_data` dict in `HouseholdStateDTO` with explicit fields.
4.  **Review Bankruptcy Phase**: Confirm if `Phase_Bankruptcy` *must* run before matching. If so, update the Spec; otherwise, move it to `Phase5_PostSequence`.
