# AUDIT REPORT: STRUCTURAL INTEGRITY (v2.0)

**Date**: 2025-05-18
**Auditor**: Jules
**Scope**: `modules/`, `simulation/`, `utils/`

## 1. Executive Summary

The structural audit reveals significant violations of the "God Class" constraint in core agent implementations (`Firm`, `Household`) and identifies potential abstraction leaks where raw agent objects are passed to decision engines (primarily in tests and via defensive coding in engines). The "Sacred Sequence" is generally respected but with notable interleaving of Lifecycle phases.

## 2. God Class Analysis

### Findings
Two primary classes exceed the 800-line limit and exhibit mixed responsibilities:

1.  **`simulation/firms.py` (Firm)**:
    -   **Lines**: 1422 (Limit: 800)
    -   **Responsibilities**: Orchestration, Lifecycle Management (`update_needs`, `check_bankruptcy`), State Management (HR, Finance, Production, Sales), Interface Implementation (`ILearningAgent`, `IFinancialFirm`, etc.).
    -   **Recommendation**: Decompose into `FirmLifecycleManager` (orchestration) and `FirmStateContainer` (state). Move logic to specialized Engines (`HREngine`, `FinanceEngine`, etc.) which is partially done but the Orchestrator retains too much glue code.

2.  **`simulation/core_agents.py` (Household)**:
    -   **Lines**: 1107 (Limit: 800)
    -   **Responsibilities**: Orchestration, Lifecycle (`update_needs`, `aging`), State Management (Bio, Econ, Social), Interface Implementation.
    -   **Recommendation**: Similar decomposition strategy as Firm. Extract `HouseholdLifecycleManager`.

3.  **`modules/finance/api.py`**:
    -   **Lines**: 1043 (Limit: 800)
    -   **Analysis**: This is a definitions file containing Protocols and DTOs. While large, it does not contain significant logic. However, splitting it into `protocols.py` and `dtos.py` would improve maintainability.

## 3. Leaky Abstractions (DTO Purity)

### Findings
The "DTO Purity" principle requires that Decision Engines receive only DTOs (`DecisionContext`), not raw Agent objects.

1.  **Production Code Compliance**:
    -   `Firm.make_decision` correctly calls `self.get_snapshot_dto()`/`self.get_state_dto()` and passes these to the context.
    -   `Household.make_decision` correctly calls `self.create_snapshot_dto()`/`self.create_state_dto()` and passes these to the context.

2.  **Abstraction Leaks (Defensive Coding)**:
    -   **`ConsumptionManager` (Household)**: The `check_survival_override` and `decide_consumption` methods contain defensive code using `isinstance` and `getattr` to handle cases where `household` might be a raw object (or a Mock behaving like one).
        ```python
        # Example from ConsumptionManager
        if isinstance(household_assets, dict):
            household_assets = household_assets.get(DEFAULT_CURRENCY, 0.0)
        else:
            household_assets = float(household_assets) # Duck typing for raw Agent
        ```
    -   **Impact**: This allows "impure" usage to persist without error, potentially masking leaks in future development.

3.  **Test Code Leaks**:
    -   Numerous unit tests (e.g., `tests/unit/decisions/test_household_engine_refactor.py`) explicitly create `MagicMock` objects that mimic raw agents and pass them as `state` in `DecisionContext`.
    -   **Recommendation**: Refactor tests to use strictly typed DTOs (`HouseholdStateDTO`, `FirmStateDTO`) instead of Mocks that mimic Agents.

## 4. Sacred Sequence Verification

The sequence `Decisions -> Matching -> Transactions -> Lifecycle` is generally followed but with interleaving.

**Observed Sequence (`TickOrchestrator`):**
1.  **`Phase1_Decision`** (Decisions)
2.  **`Phase_Bankruptcy`** (Lifecycle - Death/Liquidation)
3.  **`Phase2_Matching`** (Matching)
4.  ...
5.  **`Phase3_Transaction`** (Transactions)
6.  **`Phase_Consumption`** (Lifecycle - Consumption Finalization)
7.  **`Phase5_PostSequence`** (Lifecycle - Cleanup)

**Analysis**:
-   `Phase_Bankruptcy` (Lifecycle) occurs *before* Matching. This ensures dead agents don't trade, which is valid.
-   `Household.update_needs` (Aging/Decay) is called within `Phase_Bankruptcy`. This means needs decay happens *after* the decision phase (which used previous tick's needs). This implies a 1-tick lag in need perception relative to action, which is acceptable for discrete time steps but should be noted.

## 5. Purity Gate

-   **`BaseDecisionEngine`**: Contains a "DTO PURITY GATE" that asserts `context.state` is present.
-   **Weakness**: It does not strictly validate the *type* of `context.state`. It relies on Python's dynamic typing.
-   **Recommendation**: Enhance `BaseDecisionEngine` to strictly `isinstance` check against `HouseholdStateDTO` or `FirmStateDTO`.

## 6. Recommendations

1.  **Refactor God Classes**: Prioritize decomposing `Firm` (1422 lines) and `Household` (1107 lines).
2.  **Strict DTO Enforcement**: Remove defensive duck-typing in `ConsumptionManager` and enforce `HouseholdStateDTO`.
3.  **Test Refactoring**: Update tests to use DTO constructors instead of Mocks for state.
4.  **Sequence Documentation**: Explicitly document the "Interleaved Lifecycle" (Bankruptcy before Matching, Consumption after Transactions) as the canonical sequence.
