# Insight Report: TD-259 Government Refactor

## 1. Problem Phenomenon
The `Government` agent was implemented as a "God Class," violating the Single Responsibility Principle (SRP). It directly managed:
-   Policy decision-making (Taylor Rule, AI).
-   Policy execution (Tax collection, Welfare distribution).
-   State management (Assets, Debt, Public Opinion).
-   External system interactions (Settlement, Finance).

This tight coupling made it difficult to:
-   Test decision logic in isolation.
-   Extend policy strategies without modifying the core agent.
-   Integrate new systems (like `PublicManager`) cleanly.

## 2. Root Cause Analysis
The monolithic design stemmed from an early architectural pattern where agents were self-contained entities logic rather than orchestrators of specialized components. As the simulation complexity grew (e.g., adding `AdaptiveGovBrain`, `TaxService`), the `Government` class accumulated excessive responsibilities.

## 3. Solution Implementation Details
The `Government` agent was refactored into an **Orchestrator-Engine** pattern:

### 3.1. New Components
*   **`GovernmentDecisionEngine`**: A stateless engine responsible for determining *what* to do. It takes `GovernmentStateDTO` and `MarketSnapshotDTO` as input and outputs a `PolicyDecisionDTO`. It encapsulates the logic for `TaylorRule` and `AdaptiveGovBrain`.
*   **`PolicyExecutionEngine`**: A stateless engine responsible for *how* to execute decisions. It takes a `PolicyDecisionDTO` and a `GovernmentExecutionContext` (injecting services like `TaxService`, `WelfareManager`) and outputs an `ExecutionResultDTO`.
*   **DTOs**:
    *   `GovernmentStateDTO`: Immutable snapshot of internal state.
    *   `GovernmentSensoryDTO` (Renamed from old `GovernmentStateDTO`): External sensory data.
    *   `PolicyDecisionDTO`: High-level command.
    *   `ExecutionResultDTO`: Detailed execution outcomes (payment requests, state updates).

### 3.2. Refactored Orchestrator (`Government`)
The `Government` class now acts as a facade/orchestrator:
1.  Collects state into DTOs.
2.  Delegates decision-making to `GovernmentDecisionEngine`.
3.  Delegates execution to `PolicyExecutionEngine`, injecting necessary services via `GovernmentExecutionContext`.
4.  Applies the results (State updates, Settlement transfers).

### 3.3. Key Integrations
*   **`PublicManager`**: Integrated into `GovernmentExecutionContext` to support future asset recovery scenarios.
*   **`Market Purity`**: Engines strictly consume `MarketSnapshotDTO` and do not access raw `Market` objects.
*   **Legacy Compatibility**: Retained `run_welfare_check` and `make_policy_decision` signatures to ensure compatibility with existing orchestration phases.

## 4. Lessons Learned & Technical Debt
*   **DTO Naming**: The clash between the new internal state DTO and the existing sensory DTO (both initially named `GovernmentStateDTO`) caused confusion. Renaming the sensory one to `GovernmentSensoryDTO` clarified the distinction.
*   **Mocking Pitfalls**: Integration tests relying on strict object identity checks (e.g., `assert payee == government_obj`) failed when services returned string IDs (e.g., "GOVERNMENT"). Robust tests should handle both object identity and ID equality.
*   **Service Boundaries**: `TaxService` and `WelfareManager` are currently somewhat hybrid—logic services but also holding some flow state. Future refactoring could make them purely functional.
*   **Technical Debt**:
    *   `FinanceSystem` logic for bailouts is still partially invoked directly by `Government` because `ExecutionEngine` does not have full access to `FinanceSystem`'s internal mutation methods (like `grant_bailout_loan` returning transactions). Ideally, `FinanceSystem` should also be refactored into stateless logic + state container.
    *   `Government.potential_gdp` calculation logic is duplicated/split between `TaylorRulePolicy` (legacy) and `GovernmentDecisionEngine`.

## 5. Verification
*   **Unit Tests**: `tests/integration/test_government_refactor_behavior.py` verifies the engine interactions.
*   **Integration Tests**: `tests/integration/test_government_integration.py` passes with the refactored agent.
*   **Fiscal Policy Tests**: `tests/integration/test_fiscal_policy.py` passes (with minor test adjustments for DTOs).
