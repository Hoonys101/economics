# Insight Report: WO-LIQUIDATE-ISOLATION

## 1. Architectural Insights

### Rollback Decoupling & Protocol Hardening
The decoupling of rollback mechanics from domain objects (`Bank`, `Agent`) to the `TransactionProcessor` and `ITransactionHandler` represents a significant shift towards a stateless, service-oriented architecture.

*   **Centralized Authority**: `TransactionProcessor` is now the sole authority for dispatching rollback requests via `rollback_transaction`. It delegates to specialized handlers, removing the need for agents to know how to reverse transactions.
*   **Protocol Enforcement**: The `ITransactionHandler` protocol now explicitly includes `rollback(tx, context) -> bool`. This enforces that any new transaction type MUST consider reversibility during design.
*   **Fail-Safe Strategy**: Handlers for complex sagas (Housing, Asset Transfer) now have explicit rollback stubs that log critical warnings rather than failing silently or attempting dangerous partial reversals. This highlights areas for future "Reverse Saga" implementation.

### Analytics Purity & DTO Enforcement
The `AnalyticsSystem` has been refactored to strictly consume DTOs (`HouseholdSnapshotDTO`, `FirmStateDTO`) instead of accessing agent state directly.

*   **State Isolation**: The analytics pipeline no longer calls `get_assets_by_currency()` or other dynamic methods on agents. This prevents "Observer Effect" where analytics could theoretically mutate state or trigger lazy loading side-effects.
*   **Type Safety**: Explicit type checking (`isinstance(Household)`) and DTO construction ensures that the data shape is guaranteed before processing.

## 2. Regression Analysis

During the implementation, the following regressions/issues were identified and resolved:

1.  **Analytics Purity Violation**:
    *   **Issue**: `AnalyticsSystem` was calling `agent.get_assets_by_currency()` directly.
    *   **Fix**: Refactored `aggregate_tick_data` to instantiate `HouseholdSnapshotDTO` or `FirmStateDTO` and extract assets from there. Added `tests/unit/simulation/systems/test_analytics_system_purity.py` to enforce this constraint (verified by asserting `get_assets_by_currency` is NOT called).

2.  **Missing `IndustryDomain` Import**:
    *   **Issue**: `modules/market/api.py` failed to import `IndustryDomain`, causing `NameError` during tests.
    *   **Fix**: Added `from modules.common.enums import IndustryDomain` to `modules/market/api.py`.

3.  **Test Environment Dependencies**:
    *   **Issue**: `pytest`, `pydantic`, `pyyaml`, `joblib`, `scikit-learn` were missing in the environment.
    *   **Fix**: Installed missing dependencies to enable verification scripts.

## 3. Test Evidence

### Unit Verification: Analytics Purity
The new test `tests/unit/simulation/systems/test_analytics_system_purity.py` confirms that direct access is forbidden and DTOs are used.

```text
tests/unit/simulation/systems/test_analytics_system_purity.py::TestAnalyticsSystemPurity::test_aggregate_tick_data_uses_snapshots_only PASSED [100%]
```

### Operational Forensics
`scripts/operation_forensics.py` ran successfully, indicating the system is stable and capable of running a 60-tick simulation with the new Transaction Processor logic.

```text
Initializing Operation Forensics (STRESS TEST: Asset=50.0 for 60 ticks)...
...
Tick 60/60 complete...
💾 Raw diagnostic logs saved to logs/diagnostic_raw.csv
Simulation Complete. Analyzing 0 deaths...
📄 Forensic report saved to reports/AUTOPSY_REPORT.md
```

(Note: An existing M2 delta issue persists, as noted in Tech Debt Ledger, but no new crashes or regressions were introduced by the rollback refactor).
