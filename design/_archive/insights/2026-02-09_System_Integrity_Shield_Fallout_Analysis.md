# Technical Insight Report: Integrity Shield (Phase 12)

## 1. Problem Phenomenon
During the integration of the Orchestrator-Engine refactor, the system exhibited widespread instability manifesting in 15+ critical failures across the test suite. Key symptoms included:

*   **Import Errors:** `ImportError: cannot import name 'IConsumptionManager'` indicating broken API contracts in `modules/household/api.py`.
*   **Name Errors:** `GovernmentStateDTO` and `IShareholderRegistry` were missing, causing crashes in Government and Liquidation modules.
*   **Runtime Crashes:** `ProductionEngine` failed with `TypeError` when processing employees with uninitialized (`None`) labor skills.
*   **Protocol Violations:**
    *   Housing Settlement tests failed because transfers were missing the mandatory `currency='USD'` argument.
    *   `SettlementSystem.submit_saga` raised `AttributeError`, as the method had been moved to `SagaOrchestrator` but tests weren't updated.
*   **Mocking Failures:** Unit tests for `LiquidationManager` failed because mocks were setting legacy attributes (`firm.finance.balance`) that no longer exist on the `Firm` entity.

## 2. Root Cause Analysis
The failures stemmed from three primary sources:

1.  **Incomplete Refactoring (Dead Code & Missing APIs):**
    *   The decomposition of `Household` into Engines left the API definitions (`modules/household/api.py`) incomplete, missing key protocols used by the engines.
    *   `GovernmentStateDTO` was renamed/moved to `GovernmentSensoryDTO` in the API definition but not in consumer tests.
2.  **Architectural Drift (Saga Pattern):**
    *   The responsibility for Saga management was shifted from `SettlementSystem` to `SagaOrchestrator` (Refactor TD-160/TD-253), but integration points (tests and `HousingSystem`) were still calling the old entry point.
3.  **Strict Typing & Protocol Enforcement:**
    *   The new `IFinancialAgent` protocol enforces strict multi-currency transfers (`transfer(..., currency='USD')`). Legacy tests and some handlers were still using the implicit default, causing signature mismatches.
    *   `Firm` entity no longer exposes direct state attributes (`firm.finance`), requiring tests to mock the `IFinancialAgent` interface instead.

## 3. Solution Implementation Details

### 3.1 API & Protocol Restoration
*   **Household API:** Restored `IConsumptionManager`, `IDecisionUnit`, and `IEconComponent` protocols in `modules/household/api.py` to satisfy imports.
*   **Simulation API:** Defined `IShareholderRegistry` and `ShareholderData` in `modules/simulation/api.py` to support the Liquidation Manager.
*   **DTO Alignment:** Updated `tests/unit/modules/government/test_adaptive_gov_brain.py` to use the correct `GovernmentSensoryDTO`.

### 3.2 Logic Hardening
*   **Production Engine:** Wrapped labor skill accumulation in `ProductionEngine.execute_rd_outcome` and `produce` with `(emp.labor_skill or 0.0)` to prevent `NoneType` arithmetic errors.
*   **Settlement Sagas:** Updated `test_settlement_saga_integration.py` to instantiate and use `SagaOrchestrator` for `submit_saga` calls, aligning with the new architecture.

### 3.3 Test Suite Alignment
*   **Housing Handlers:** Updated all `settlement_system.transfer` assertions in housing tests to expect `currency='USD'`.
*   **Commerce System:** Renamed `execute_consumption_and_leisure` to `finalize_consumption_and_leisure` in tests to match the implementation.
*   **Liquidation Manager:** Refactored tests to mock `Firm` correctly using `spec=Firm` and `get_liquidation_config`, removing references to non-existent attributes like `firm.finance.balance`.
*   **Firm Management:** Corrected assertions in leak tests (`test_firm_management_leak.py`) to expect `initial_capital` to be `None` (default) rather than `0.0`.

## 4. Lessons Learned & Technical Debt

*   **Mocking Risks:** Tests relying on `MagicMock()` without `spec` disguised architectural changes (like attribute removal). Future tests should strictly use `spec=Class` to catch regression immediately.
*   **Refactor Synchronization:** When moving core responsibilities (like Saga submission), a "find-all-references" pass is critical. The `submit_saga` artifact remained in multiple test files despite the logic moving.
*   **Protocol Purity:** The shift to `IFinancialAgent` requires disciplined currency handling. The codebase is currently in a hybrid state where some components assume 'USD' default and others require explicit passing. This should be standardized.

### Identified Technical Debt
*   **Hybrid Saga Handling:** Some legacy handlers might still be tightly coupled to `SettlementSystem` rather than `SagaOrchestrator`. A full audit of `ISagaHandler` implementations is recommended.
*   **Currency Ubiquity:** `DEFAULT_CURRENCY` is imported from `modules.system.api` but string literals 'USD' are used in tests. These should be unified to prevent future refactor breakage.
