# AUDIT_REPORT_STRUCTURAL: Structural Integrity Audit

**Date**: 2025-05-18
**Auditor**: Jules
**Scope**: `simulation/`, `modules/`

## 1. Executive Summary
This audit validates the structural integrity of the codebase against the DTO-based Decoupling and Component SoC architecture. The audit focused on identifying God Classes, tracing raw agent leaks into decision engines, and verifying the "Sacred Sequence" of simulation ticks.

**Key Findings:**
*   **God Classes**: 2 primary God Classes identified (`Firm`, `Household`) exceeding 800 lines.
*   **Raw Agent Leaks**: No direct leaks found in `DecisionContext`, but internal component leaks exist in `HREngine` (accessing `Household` via interface). A DTO signature mismatch bug was found in `FinancialStrategy`.
*   **Sequence Violation**: The `TickOrchestrator` executes Lifecycle phases (`Bankruptcy`, `SystemicLiquidation`) before `Matching`, violating the standard `Decisions -> Matching -> Transactions -> Lifecycle` sequence.

## 2. God Class Analysis
The following files exceed the 800-line threshold or exhibit mixed domain responsibilities.

| File | Lines | Class | Description | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| `simulation/firms.py` | 1303 | `Firm` | Orchestrator for all firm logic (Production, HR, Finance, Sales). Contains complex state management and delegation logic. | Decompose `Firm` into smaller, specialized orchestrators or move more logic into stateless engines. |
| `simulation/core_agents.py` | 1046 | `Household` | Orchestrator for household logic (Labor, Consumption, Asset Management). Mixes biological, economic, and social concerns. | Further decompose `Household` by extracting `BioComponent`, `SocialComponent` management into separate handlers. |
| `modules/finance/api.py` | 884 | N/A | Contains multiple Protocols and DTO definitions. Not a single class, but a large API definition file. | Acceptable as an API aggregation file, but consider splitting by sub-domain if it grows further. |

## 3. Leaky Abstraction Trace
Trace analysis of `DecisionContext` and `make_decision` calls to verify DTO usage.

### 3.1 Decision Context Purity
*   **Status**: **PASS**
*   **Verification**: `DecisionContext` strictly enforces `state` as `Union[HouseholdStateDTO, FirmStateDTO]`.
*   **Evidence**:
    *   `Firm.make_decision` calls `self.get_state_dto()` (returns `FirmStateDTO`) and passes it to `DecisionContext`.
    *   `Household.make_decision` calls `self.create_state_dto()` (returns `HouseholdStateDTO`) and passes it to `DecisionContext`.

### 3.2 Decision Engine Analysis
*   **RuleBasedFirmDecisionEngine**: **PASS**. Uses `FirmStateDTO` exclusively.
*   **AIDrivenFirmDecisionEngine**: **PASS**. Passes `FirmStateDTO` to `CorporateManager` and Strategies.
*   **RuleBasedHouseholdDecisionEngine**: **PASS**. Uses `HouseholdStateDTO` exclusively.
*   **AIDrivenHouseholdDecisionEngine**: **PASS**. Uses `HouseholdStateDTO` exclusively.

### 3.3 Identified Leaks & Anomalies
*   **HREngine (Internal Component Leak)**:
    *   `HREngine` methods accept `HRState` which contains `List[IEmployeeDataProvider]`. `IEmployeeDataProvider` is implemented by `Household`.
    *   **Impact**: `HREngine` has access to raw `Household` instance properties (e.g., `labor_skill`), creating a coupling between Firm internals and Household implementation.
    *   **Recommendation**: Replace `IEmployeeDataProvider` usage in `HRState` with a lightweight DTO (e.g., `EmployeeSnapshotDTO`) that is updated during the tick.

*   **FinancialStrategy (Bug/Purity Issue)**:
    *   `FinancialStrategy._manage_debt` constructs `BorrowerProfileDTO` with fields `borrower_id` and `existing_assets` which are **removed** from the definition in `modules/finance/api.py`.
    *   **Impact**: Runtime error or attribute error if strict type checking is enabled.
    *   **Recommendation**: Update `FinancialStrategy` to match the current `BorrowerProfileDTO` signature.

## 4. Sacred Sequence Verification
Verification of the simulation tick execution order in `TickOrchestrator`.

**Standard Sequence**: `Decisions -> Matching -> Transactions -> Lifecycle`

**Actual Sequence**:
1.  `Phase1_Decision` (Decisions)
2.  **`Phase_Bankruptcy` (Lifecycle)** - *Violation*
3.  **`Phase_SystemicLiquidation` (Lifecycle)** - *Violation*
4.  `Phase2_Matching` (Matching)
5.  ...
6.  `Phase3_Transaction` (Transactions)
7.  `Phase_Consumption` (Lifecycle)

**Analysis**:
*   `Phase_Bankruptcy` and `Phase_SystemicLiquidation` are Lifecycle phases but run **before** `Phase2_Matching`.
*   **Justification (Potential)**: Bankrupt agents must be removed or frozen before they attempt to trade in the Matching phase.
*   **Verdict**: **VIOLATION**. While logically defensible for simulation stability, it violates the architectural "Sacred Sequence".
*   **Recommendation**:
    *   Option A: Reclassify Bankruptcy/Liquidation as a pre-matching filtering step (e.g., "Phase 1.5: Solvency Check").
    *   Option B: Move Bankruptcy/Liquidation to the Lifecycle phase (after Transactions) and ensure the Matching engine gracefully handles insolvent agents (or agents checks solvency before ordering).

## 5. Structural Module Status
*   **Firm Structure**: Uses internal state objects (`HRState`, `SalesState`) which couples `Firm` implementation to specific Engine implementations (`HREngine`, `SalesEngine`). Engines are stateless but depend on these specific state classes.
*   **Household Structure**: Similar pattern (`BioStateDTO`, `EconStateDTO` used as internal state). Engines are stateless.

## 6. Recommendations
1.  **Prioritize Decomposition**: Break down `Firm` and `Household` classes.
2.  **Fix FinancialStrategy**: Update `BorrowerProfileDTO` usage immediately.
3.  **Review Sequence**: Formalize the position of Bankruptcy/Liquidation phases. If they must run before Matching, update the "Sacred Sequence" definition or create a specific "Pre-Matching Validation" phase.
4.  **Harden HREngine**: Decouple `HREngine` from raw `Household` instances by introducing an `EmployeeDTO`.
