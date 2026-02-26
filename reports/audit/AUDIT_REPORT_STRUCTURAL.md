# AUDIT_REPORT_STRUCTURAL: Structural Integrity Audit (v2.0)

**Date**: 2024-05-24
**Scope**: Structural Integrity Audit based on `design/3_work_artifacts/specs/AUDIT_SPEC_STRUCTURAL.md`
**Focus**: God Class & Abstraction Leak

## 1. Executive Summary

The structural audit reveals a mixed picture. While significant progress has been made in decomposing logic into stateless engines (e.g., `FinanceEngine`, `HREngine`, `ProductionEngine`), the primary agent classes (`Firm`, `Household`) remain monolithic "Orchestrators" or "Facades" that aggregate state and delegate logic.

-   **God Classes Identified**: 3 classes exceed 800 lines or mix 3+ domain responsibilities.
-   **Abstraction Leaks**: Minimal. Most decision logic correctly uses DTOs (`DecisionContext`, `FirmStateDTO`, `HouseholdStateDTO`). A minor leak exists in `WelfareService` relying on implicit agent properties.
-   **Sacred Sequence**: Adherence to `Decisions -> Matching -> Transactions -> Lifecycle` appears generally enforced by the `TickOrchestrator` (implied by file structure and engine separation), though explicit verification of `tick_scheduler.py` was out of scope for this scan.

## 2. God Class Analysis

### 2.1. `simulation/firms.py` (1843 lines) - CRITICAL
The `Firm` class acts as a massive orchestrator. While it delegates logic to engines, it:
1.  **Holds All State**: Initializes and manages `HRState`, `FinanceState`, `ProductionState`, `SalesState`, `InventoryComponent`, `FinancialComponent`.
2.  **Facade Properties**: Exposes dozens of properties (e.g., `current_production`, `total_debt`) that merely delegate to internal state objects, inflating line count.
3.  **Multiple Interfaces**: Implements 13 protocols including `IOrchestratorAgent`, `IFinancialFirm`, `ILiquidatable`, `ICreditFrozen`, `IInventoryHandler`, `ICurrencyHolder`, `ISensoryDataProvider`, `IConfigurable`, `IPropertyOwner`, `IFirmStateProvider`, `ISalesTracker`, `IBrainScanReady`, `ILobbyist`.

**Recommendation**:
-   Decompose `Firm` into distinct component classes that handle their own interface implementations where possible (e.g., `InventoryHandler` handling `IInventoryHandler` directly, rather than `Firm` delegating).
-   Use composition over inheritance/facade.

### 2.2. `simulation/core_agents.py` (1246 lines) - HIGH
The `Household` class similarly aggregates:
1.  **Bio/Econ/Social State**: Manages `BioStateDTO`, `EconStateDTO`, `SocialStateDTO`.
2.  **Engine Delegation**: Delegates to `LifecycleEngine`, `NeedsEngine`, `SocialEngine`, `BudgetEngine`, `ConsumptionEngine`, `BeliefEngine`, `CrisisEngine`.
3.  **Interface Bloat**: Implements `ILearningAgent`, `IEmployeeDataProvider`, `IEducated`, `IHousingTransactionParticipant`, `IFinancialEntity`, `IOrchestratorAgent`, `ICreditFrozen`, `IInventoryHandler`, `ISensoryDataProvider`, `IInvestor`, `IVoter`.

**Recommendation**:
-   Similar to `Firm`, decompose into components.

### 2.3. `simulation/systems/settlement_system.py` (921 lines) - MEDIUM
The `SettlementSystem` manages:
1.  **Transaction Execution**: Atomicity, Zero-Sum checks.
2.  **Registry Lookups**: Accounts, Agents, Estates.
3.  **Side Effects**: Estate Distribution hooks.
4.  **Reporting**: M2 Audit, Panic Recording.

While large, it acts as a central infrastructure component. Its size is driven by the complexity of maintaining financial integrity across the entire simulation.

**Recommendation**:
-   Extract `AccountRegistry` logic fully (it seems partially extracted).
-   Move M2 Audit logic to a dedicated `MonetaryAuditor` service.

## 3. Abstraction Leak Analysis

### 3.1. Decision Context (COMPLIANT)
-   **Household**: `make_decision` creates `DecisionContext` using `legacy_state_dto` (a `HouseholdStateDTO`), passing a snapshot rather than `self`.
    ```python
    # simulation/core_agents.py
    snapshot_dto = self.create_snapshot_dto()
    legacy_state_dto = self.create_state_dto()
    context = DecisionContext(state=legacy_state_dto, ...)
    ```
-   **Firm**: `make_decision` constructs `DecisionInputDTO` and calls engines (`finance_engine`, `hr_engine`) with specific context DTOs (`FinanceDecisionInputDTO`, `HRContextDTO`). It does *not* pass `self` to engines.
    ```python
    # simulation/firms.py
    snapshot = self.get_snapshot_dto()
    fin_input = FinanceDecisionInputDTO(firm_snapshot=snapshot, ...)
    budget_plan = self.finance_engine.plan_budget(fin_input)
    ```

### 3.2. Welfare Service (MINOR LEAK)
-   **Observation**: `WelfareService.run_welfare_check` iterates over `agents: List[IAgent]` and checks `if hasattr(agent, "is_employed")`.
    ```python
    # modules/government/services/welfare_service.py
    if hasattr(agent, "is_employed") and not agent.is_employed:
        # ...
    ```
-   **Issue**: `is_employed` is not part of `IAgent` or `IWelfareRecipient` protocol. This relies on implicit knowledge of `Household` structure.
-   **Recommendation**: Add `is_employed` to `IWelfareRecipient` protocol or a new `IEmployable` interface.

### 3.3. Government Support (ACCEPTABLE)
-   **Observation**: `Government.provide_household_support` passes `household` (Agent object) to `SettlementSystem.transfer`.
-   **Justification**: `SettlementSystem.transfer` expects `IFinancialEntity`. `Household` implements this protocol. This is a type-safe interaction via protocol, not a raw object leak to a decision engine.

## 4. Module & Interface Health

### 4.1. `modules/finance/api.py` (1122 lines)
-   **Status**: Interface God File.
-   **Analysis**: Contains definition of all financial protocols (`IFinancialEntity`, `IBank`, `ISettlementSystem`, etc.) and DTOs.
-   **Verdict**: Acceptable for a central API definition file, but could be split into `modules/finance/protocols.py` and `modules/finance/dtos.py` for better maintainability.

### 4.2. Decision Engines
-   **Status**: Healthy.
-   **Analysis**: `RuleBasedFirmDecisionEngine`, `AIDrivenHouseholdDecisionEngine`, etc., all strictly import and use DTOs (`FirmStateDTO`, `HouseholdStateDTO`). Usage of `Firm` or `Household` classes is restricted to `TYPE_CHECKING` blocks or instantiation of results, not decision logic input.

## 5. Conclusion

The structural integrity regarding "DTO-based Decoupling" is strong in the critical `Decision Engine` layer. The "God Class" issue is primarily a result of the "Orchestrator" pattern where a single agent class aggregates all components and exposes a unified interface to the system.

**Next Steps**:
1.  **Refactor `WelfareService`**: Formalize `is_employed` in a protocol.
2.  **Decompose Orchestrators**: Move away from Facade properties in `Firm` and `Household`. Allow components to be accessed directly or via specific interfaces, reducing the main file size.
