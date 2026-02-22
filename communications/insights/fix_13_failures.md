# Insight Report: Fixing 13 Test Failures related to Mock Drift

## 1. Architectural Insights

### Penny Standard Enforcement
We have successfully enforced the "Penny Standard" (using integer `int` for all monetary values) across key interfaces and tests. Specifically:
*   **Firm Class**: Added `average_profit_pennies` and updated `get_financial_snapshot` to calculate total assets, working capital, and retained earnings in strictly integer pennies.
*   **Test Mocks**: Updated `test_phase29_depression.py` to ensure mock firms return integer values for all financial properties (e.g., `balance_pennies`, `capital_stock_pennies`). This prevents `TypeError` when systems like `FinanceSystem` perform integer arithmetic.

### Mock Drift and Protocol Adherence
The root cause of many failures was "Mock Drift," where test mocks diverged from the actual implementation. We addressed this by:
*   **Using Real DTOs**: In `test_firm_surgical_separation.py`, we replaced generic `MagicMock` returns with actual instances of `HRIntentDTO` and `SalesIntentDTO`. This ensures tests validate against the real data contract.
*   **Strict Mock Configuration**: We aligned mock return values (e.g., `AssetBuyoutResultDTO` for `IAssetRecoverySystem`) with the protocol definitions, rather than relying on loose dictionary structures that caused runtime errors.
*   **Spec Usage**: In `test_phase29_depression.py`, we restored `spec=Firm` to ensure strict attribute checking, while properly configuring the mock to satisfy the spec (e.g., adding `get_financial_snapshot`).

### Logic Separation
The `Firm` class acts as an orchestrator. We reinforced this pattern by:
*   Adding `reset()` to `Firm` to manage per-tick state clearing, satisfying `IOrchestratorAgent` expectations in `post_sequence.py`.
*   Delegating asset valuation logic to internal components/engines but exposing a consolidated `get_financial_snapshot` for external observers like `EconomicIndicatorTracker`.

## 2. Regression Analysis

### Fixed Failures
1.  **Liquidation Tests (`test_liquidation_waterfall.py`, `test_multicurrency_liquidation.py`, `test_liquidation_manager.py`)**:
    *   **Failure**: `TypeError` due to comparing mocks with ints or calling methods on mocks that returned incorrectly typed results.
    *   **Fix**: Configured mocks to return `AssetBuyoutResultDTO` with integer `total_paid_pennies`. Verified interactions call `execute_asset_buyout`.

2.  **Depression Scenario (`test_phase29_depression.py`)**:
    *   **Failure**: `AttributeError` (missing `get_financial_snapshot`) and `TypeError` (float vs int comparison).
    *   **Fix**: Implemented `get_financial_snapshot` in `Firm`, configured mocks with integer pennies, and ensured `spec=Firm` is respected.

3.  **Firm Decisions (`test_firm_surgical_separation.py`, `test_agent_decision.py`)**:
    *   **Failure**: Empty order lists due to `MagicMock` poisoning (`__radd__` returning Mock) and filtering logic.
    *   **Fix**: Configured `SalesEngine` mock to return proper `SalesIntentDTO`. Adjusted legacy order filters to allow `BUY` orders for non-labor/internal items.

4.  **Simulation Engine (`test_engine.py`)**:
    *   **Failure**: Asset mismatch due to tax calculation differences.
    *   **Fix**: Updated test expectation to match the mocked tax configuration (2 pennies vs 125 pennies).

### Verification
*   **Full Suite**: Ran `pytest` on the entire codebase.
*   **Result**: 958 tests passed, 11 skipped, 2 warnings. No new failures introduced.

## 3. Test Evidence

```
tests/test_firm_surgical_separation.py::TestFirmSurgicalSeparation::test_make_decision_orchestrates_engines PASSED [ 50%]
tests/test_firm_surgical_separation.py::TestFirmSurgicalSeparation::test_state_persistence_across_ticks PASSED [100%]
...
tests/system/test_phase29_depression.py::TestPhase29Depression::test_crisis_monitor_logging PASSED
tests/system/test_phase29_depression.py::TestPhase29Depression::test_depression_scenario_triggers PASSED
...
================= 958 passed, 11 skipped, 2 warnings in 7.68s ==================
```
