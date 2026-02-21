# Wave 7 Insight Report: Firm Mutation (Stateless Engine Orchestration)

## 1. Architectural Insights

### Technical Debt Identified
The `Firm` agent (`simulation/firms.py`) exhibited "God Class" symptoms, acting as both an orchestrator and a container for business logic that mutated state across multiple domains (Finance, HR, Sales, Brand). While some engines like `ProductionEngine` and `AssetManagementEngine` were stateless and purely functional, others like `FinanceEngine` and `BrandEngine` relied on side-effects, mutating the state objects passed to them.

Specifically:
- `BrandEngine.update` mutated `SalesState` in-place.
- `SalesEngine.post_ask` mutated `SalesState.last_prices`.
- `SalesEngine.check_and_apply_dynamic_pricing` mutated the `orders` list in-place and `SalesState.last_prices`.

This violated the "Stateless Engine Orchestration" principle, where engines should be pure functions (Input -> Output) and the Orchestrator (`Firm`) should be responsible for applying state changes.

### Architectural Decisions
To enforce the new architecture:
1.  **Protocol Purity**: All engines must explicitly inherit from their `modules.firm.api` protocols. Runtime `isinstance` checks are enforced in `Firm.__init__`.
2.  **Stateless Engines**: `BrandEngine` and `SalesEngine` are refactored to be purely functional. They now return DTOs (`BrandMetricsDTO`, `DynamicPricingResultDTO`) instead of mutating state.
3.  **DTO Expansion**: `SalesStateDTO` was expanded to include `adstock`, enabling `BrandEngine` to calculate new metrics without accessing the mutable `SalesState` object.
4.  **Orchestrator Responsibility**: The `Firm` agent now explicitly handles the application of results returned by engines, ensuring a clear separation of concerns (Logic vs. State Application).

## 2. Regression Analysis

### Broken Tests & Fixes
-   **`test_sales_engine_refactor.py`**: Expected to fail initially because it likely asserts side-effects (e.g., `state.last_prices` updated after `post_ask`).
    -   *Fix*: Updated tests to verify that `post_ask` returns an order without side-effects, and that the Orchestrator (mocked or real) applies the changes.
-   **`test_wo157_dynamic_pricing.py`**: Expected to fail because it checks for in-place modification of `orders`.
    -   *Fix*: Updated tests to assert the returned `DynamicPricingResultDTO` contains the modified orders and price updates.

## 3. Test Evidence

```
tests/unit/test_wo157_dynamic_pricing.py::TestWO157DynamicPricing::test_record_sale_updates_tick PASSED [  7%]
tests/unit/test_wo157_dynamic_pricing.py::TestWO157DynamicPricing::test_dynamic_pricing_reduction PASSED [ 15%]
tests/unit/test_wo157_dynamic_pricing.py::TestWO157DynamicPricing::test_dynamic_pricing_floor PASSED [ 23%]
tests/unit/test_wo157_dynamic_pricing.py::TestWO157DynamicPricing::test_dynamic_pricing_not_stale PASSED [ 30%]
tests/unit/test_wo157_dynamic_pricing.py::TestWO157DynamicPricing::test_transaction_processor_calls_record_sale
-------------------------------- live log call ---------------------------------
WARNING  simulation.systems.handlers.goods_handler:goods_handler.py:123 GOODS_HANDLER_WARN | Buyer <Mock name='mock.id' id='139628550683248'> does not implement IInventoryHandler
PASSED                                                                   [ 38%]
tests/test_firm_surgical_separation.py::TestFirmSurgicalSeparation::test_make_decision_orchestrates_engines PASSED [ 46%]
tests/test_firm_surgical_separation.py::TestFirmSurgicalSeparation::test_state_persistence_across_ticks
-------------------------------- live log call ---------------------------------
INFO     modules.firm.orchestrators.firm_action_executor:firm_action_executor.py:147 INTERNAL_EXEC | Firm 1 fired employee 101.
PASSED                                                                   [ 53%]
tests/unit/components/test_engines.py::TestHREngine::test_create_fire_transaction
-------------------------------- live log call ---------------------------------
WARNING  simulation.components.engines.hr_engine:hr_engine.py:379 INTERNAL_EXEC | Firm 1 cannot afford severance to fire 101.
PASSED                                                                   [ 61%]
tests/unit/components/test_engines.py::TestHREngine::test_process_payroll PASSED [ 69%]
tests/unit/components/test_engines.py::TestSalesEngine::test_post_ask PASSED [ 76%]
tests/unit/components/test_engines.py::TestSalesEngine::test_generate_marketing_transaction PASSED [ 84%]
tests/unit/components/test_engines.py::TestFinanceEngine::test_generate_financial_transactions PASSED [ 92%]
tests/unit/components/test_engines.py::TestProductionEngine::test_produce_depreciation PASSED [100%]

=============================== warnings summary ===============================
../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 13 passed, 2 warnings in 0.55s ========================
```
