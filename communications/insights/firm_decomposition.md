# Firm Decomposition Insights

## Summary
The decomposition of the `Firm` agent into specialized engines (`ProductionEngine`, `AssetManagementEngine`, `RDEngine`) and the refactoring of `Firm` into a pure orchestrator has been completed.

## Architecture Improvements
1.  **Stateless Engines**: The new engines are purely functional and stateless, operating on `FirmSnapshotDTO` and returning result DTOs. This significantly improves testability and modularity.
2.  **Orchestrator Pattern**: The `Firm` class now strictly orchestrates logic by delegating to engines and applying results to its state. The God Method `_execute_internal_order` has been replaced by a structured `execute_internal_orders` loop.
3.  **Protocol Alignment**: The canonical `IInventoryHandler` protocol is now consistent across the codebase, and `ICollateralizableAsset` has been introduced for advanced asset management.
4.  **DTO Purity**: All cross-boundary communication now uses typed DTOs defined in `modules/firm/api.py`.

## Technical Debt & Observations
1.  **State Management**: `Firm` still maintains mutable state objects (`ProductionState`, `FinanceState`, etc.). While engines are stateless, the orchestrator still manually updates these state objects based on engine results. A future improvement could be to make state objects immutable and have engines return new state instances (State Reducer pattern).
2.  **Legacy Components**: `RealEstateUtilizationComponent` and `BrandManager` are still instantiated and managed directly within `Firm`. These could be candidates for future extraction into their own engines or services.
3.  **Property Accessors**: `Firm` retains many property accessors that route to internal state DTOs for backward compatibility. These should be deprecated over time in favor of accessing state DTOs directly via `get_state_dto()`.
4.  **Depreciation Logic**: `ProductionEngine` previously applied depreciation as a side effect. This logic was moved to be calculated by the engine but returned as `capital_depreciation` and `automation_decay` values in `ProductionResultDTO`, which the `Firm` orchestrator then applies. This maintains statelessness but requires the orchestrator to handle the update.

## Risks
1.  **Performance**: Constructing `FirmSnapshotDTO` on every tick/decision might have a slight overhead, but it ensures data consistency for engines.
2.  **Integration**: While unit tests cover the new logic extensively, full integration with the simulation loop (dependent on `yaml` config loading) needs verification in a full environment.
