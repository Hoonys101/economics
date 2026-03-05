# Phase 22 [W2]: Financial Integrity & Saga Recovery (WO-LIQUID-W2-FINANCE)

## 1. Architectural Insights
*   **M2 Definition Refinement**: The `calculate_total_money` logic was overhauled to explicitly separate **System Debt** (negative balances from Soft Budget Agents like `PublicManager`) from **Circulating Money** (M2). Previously, negative balances were netted against positive cash, artificially lowering M2 and triggering false-positive leak alarms. The new audit contract returns `{DEFAULT_CURRENCY: m2_int, "SYSTEM_DEBT": debt_int}`.
*   **Protocol-Driven Rollback**: The `CommandService` rollback logic was hardened by enforcing the `IRestorableRegistry` protocol. We removed brittle `hasattr` checks for implementation details like `delete_layer` and standardized on `delete_entry` (for creation rollback) and `restore_entry` (for modification rollback). To ensure clean state restoration in layered registries, modification rollback now explicitly clears the key before restoring the snapshot.
*   **Accounting Gap (Asset Swaps)**: A subtle accounting flaw was identified where raw material purchases by Firms were being double-counted as expenses—once upon purchase (via `GoodsTransactionHandler`) and again upon usage (via `FinanceEngine.record_expense` during production). We updated the handler to treat raw material acquisition as a pure Asset Swap (Cash -> Inventory), reserving expense recognition for the actual consumption event (COGS).
*   **Market Float Truncation**: The `MatchingEngine` (both Stock and OrderBook) was refactored to use `int(round(...))` instead of integer truncation (`//`) for mid-price calculations. This eliminates a systemic deflationary bias ("Penny Shaving") where fractional values were consistently destroyed.

## 2. Regression Analysis
*   **Rollback Failure in `CommandService`**:
    *   **Issue**: `test_rollback_set_param_preserves_origin` failed because `restore_entry` in `GlobalRegistry` only updated the specific layer passed to it, failing to remove the higher-priority `GOD_MODE` layer added by the command being rolled back.
    *   **Fix**: Modified `CommandService.rollback_last_tick` to explicitly call `registry.delete_entry(key)` before `registry.restore_entry(...)`. This ensures the state is wiped clean before the snapshot is reinstated, guaranteeing the removal of any overriding layers.
*   **Saga Orchestrator Spam**:
    *   **Issue**: `SagaOrchestrator` logged thousands of `SAGA_SKIP` warnings for dead agents but kept the invalid sagas in the active queue.
    *   **Fix**: Changed logic to `SAGA_CANCELLED` and immediately removed the saga from `active_sagas` if critical participants are invalid/missing.

## 3. Test Evidence
```text
============================= test session starts ==============================
platform linux -- Python 3.12.8, pytest-8.3.4, pluggy-1.5.0
rootdir: /app
configfile: pytest.ini
plugins: anyio-4.8.0, asyncio-0.25.3, cov-6.0.0
asyncio: mode=Mode.STRICT
collected 129 items

tests/unit/finance/test_settlement_atomic.py ....                        [  3%]
tests/unit/finance/test_settlement_fx_swap.py ..                         [  4%]
tests/unit/finance/test_settlement_integrity.py .....                    [  8%]
tests/unit/systems/test_accounting_system.py .                           [  9%]
tests/unit/systems/test_analytics_system.py .                            [ 10%]
tests/unit/systems/test_central_bank_system.py ....                      [ 13%]
tests/unit/systems/test_commerce_system.py .                             [ 13%]
tests/unit/systems/test_demographic_manager.py ....                      [ 17%]
tests/unit/systems/test_event_system.py .                                [ 17%]
tests/unit/systems/test_firm_management.py ...                           [ 20%]
tests/unit/systems/test_generational_wealth_audit.py ..                  [ 21%]
tests/unit/systems/test_housing_system.py ....                           [ 24%]
tests/unit/systems/test_immigration_manager.py ...                       [ 27%]
tests/unit/systems/test_inheritance_manager.py ....                      [ 30%]
tests/unit/systems/test_labor_market_analyzer.py .....                   [ 34%]
tests/unit/systems/test_lifecycle_manager.py ....                        [ 37%]
tests/unit/systems/test_liquidation_manager.py ....                      [ 40%]
tests/unit/systems/test_ma_manager.py ....                               [ 43%]
tests/unit/systems/test_ministry_of_education.py ...                     [ 45%]
tests/unit/systems/test_perception_system.py ...                         [ 48%]
tests/unit/systems/test_persistence_manager.py ....                      [ 51%]
tests/unit/systems/test_registry.py ....                                 [ 54%]
tests/unit/systems/test_sensory_system.py ....                           [ 57%]
tests/unit/systems/test_settlement_saga_integration.py ......            [ 62%]
tests/unit/systems/test_settlement_system.py ........................... [ 82%]
.......                                                                  [ 88%]
tests/unit/systems/test_social_system.py ..                              [ 89%]
tests/unit/systems/test_system_effects_major_choice.py ..                [ 91%]
tests/unit/systems/test_tax_agency.py .....                              [ 95%]
tests/unit/systems/test_technology_manager.py ....                       [ 98%]
tests/system/test_command_service_rollback.py ...                        [100%]

============================= 129 passed in 4.52s ==============================
```
