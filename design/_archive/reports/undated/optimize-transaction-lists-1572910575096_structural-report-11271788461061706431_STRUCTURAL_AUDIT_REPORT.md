# Structural Audit Report

## 1. God Classes (> 800 lines)

The following classes exceed the 800-line threshold, indicating a violation of the Single Responsibility Principle and potentially acting as "God Classes".

- **Firm** in `./simulation/firms.py`: 1276 lines (AST count)
    - **Responsibilities**: Orchestrates Production, Finance, HR, Sales, and R&D. While logic is delegated to stateless engines (`HREngine`, `FinanceEngine`, etc.), the class remains large due to extensive property delegation, state management, and interface implementation (`IFinancialEntity`, `IOrchestratorAgent`, etc.).
    - **Recommendation**: Continue decomposition. Move `BrandManager` to a dedicated component. Consider extracting `RealEstateUtilizationComponent` further.

- **Household** in `./simulation/core_agents.py`: 1042 lines (AST count)
    - **Responsibilities**: Orchestrates Bio, Econ, and Social aspects. Delegates to `LifecycleEngine`, `NeedsEngine`, etc.
    - **Recommendation**: Similar to Firm, continue moving logic to engines. The `Legacy Mixin Methods` section suggests further refactoring opportunities.

## 2. Abstraction Leaks (DTO Pattern)

The audit scanned for direct passing of `Household` or `Firm` instances into `DecisionContext`.

- **DecisionContext**: **PASSED**. No direct instantiation with raw agents found in source code. `DecisionContext` definition strictly enforces DTOs (`HouseholdStateDTO`, `FirmStateDTO`).
    - *Note*: Some legacy tests mocks pass raw agents, but this is a test-only artifact and does not affect production logic.

- **Manual Findings**:
    - **LiquidationContext** (`modules/finance/api.py`): Uses `IFinancialEntity` (Government) which is an interface implemented by the Agent. While this limits surface area, it technically passes the agent reference.
    - **FiscalContext** (`simulation/dtos/api.py`): Uses `IFinancialEntity` (Government). This is an acceptable trade-off for now but should ideally be a `FiscalService` or Snapshot.

## 3. Sacred Sequence Verification

Verified the execution order in `TickOrchestrator` (`simulation/orchestration/tick_orchestrator.py`).

- **Sequence Found**:
    1. `Phase_Production`
    2. `Phase1_Decision` (Decisions)
    3. `Phase_Bankruptcy` (Lifecycle Part 1)
    4. `Phase_HousingSaga`
    5. `Phase_SystemicLiquidation`
    6. `Phase2_Matching` (Matching)
    7. `Phase_BankAndDebt`
    8. `Phase_FirmProductionAndSalaries`
    ...
    13. `Phase3_Transaction` (Transactions)
    14. `Phase_Consumption` (Lifecycle Part 2)

- **Verdict**: **PASSED**. The critical sequence `Decisions -> Matching -> Transactions` is preserved. Lifecycle operations are distributed around this core sequence as appropriate (Bankruptcy early, Consumption late).

## 4. Conclusion

The codebase shows significant progress in decoupling via the Orchestrator-Engine pattern. However, the `Firm` and `Household` classes remain large orchestrators. The "God Class" risk is mitigated by the fact that they primarily delegate to stateless engines, but their size makes them hard to maintain. The "Abstraction Leak" risk is well-managed in the core decision loop (`DecisionContext`), though minor interface-based leaks exist in peripheral contexts.