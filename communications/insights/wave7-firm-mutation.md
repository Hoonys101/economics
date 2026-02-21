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

(To be populated after implementation and verification run)
