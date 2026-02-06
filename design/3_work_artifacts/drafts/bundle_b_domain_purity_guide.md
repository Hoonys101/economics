# Mission Guide: Housing Saga & Inventory Domain Purity (Track B)

## 1. Objectives
- **TD-255**: Refactor `HousingTransactionSagaStateDTO` to remove raw agent references and use a serializable `context`.
- **TD-256**: Implement `IInventoryHandler` for `HousingService` and update `saga_handler.py`.
- **TD-259**: Implement `FinanceAssetUtil` and refactor AI asset access.

## 2. Reference Context (MUST READ)
- **Primary Spec**: [spec_domain_dto_purity.md](file:///c:/coding/economics/design/3_work_artifacts/specs/spec_domain_dto_purity.md)
- **Implementation Plan**: [implementation_plan_sec5.md](file:///c:/coding/economics/brain/becf7013-8d5e-43c8-8052-cd658d3936ea/implementation_plan_sec5.md)

## 3. Implementation Roadmap
### Phase 1: Pure DTOs & Context Prefetch
- Update `modules/finance/sagas/housing_api.py` with the new DTO structure.
- Refactor `HousingTransactionSagaHandler._handle_initiated` to pre-fetch all agent data.

### Phase 2: Inventory Abstraction
- Define `IInventoryHandler` in `modules/inventory/api.py`.
- Update `HousingService` to implement the interface.
- Refactor `saga_handler.py` to use `IInventoryHandler`.

### Phase 3: AI Asset Unification
- Implement `get_asset_balance` in `modules/finance/util/api.py`.
- Refactor `AITrainingManager` and other evaluators to use this utility.

## 4. Verification
- Run `stress_test_validation` scenario.
- Perform tick-by-tick DTO snapshot comparison against golden logs.
- Verify all `hasattr(agent, 'assets')` calls in logic are replaced by the utility.
