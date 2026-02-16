# Insight Report: Firm Structure & Engine Fixes

## Architectural Insights
We have successfully refactored the `Firm` agent (formerly a "God Class") into a composed orchestrator using the **CES Lite Pattern (Component-Entity-System)**.

### Component Decomposition
- **`IInventoryComponent`**: Now encapsulates all raw inventory dictionaries (`_inventory`, `_input_inventory`) and quality logic. The `Firm` agent delegates all `IInventoryHandler` calls to this component.
- **`IFinancialComponent`**: Wraps the `Wallet` and implements `IFinancialAgent` and `IFinancialEntity`. This enforces strict penny-based arithmetic and encapsulates financial state.

### Protocol Purity
- New protocols in `modules/firm/api.py` are decorated with `@runtime_checkable` to ensure `isinstance` checks work correctly, reinforcing the "Protocol Purity" guardrail.
- `Firm` now strictly adheres to these protocols via delegation.

## Test Evidence

### 1. Engine Unit Tests (`test_asset_management_engine.py`)
Fixed the unit mismatch (pennies vs percentage scaling).

```
tests/simulation/components/engines/test_asset_management_engine.py::test_invest_automation_success PASSED [ 20%]
tests/simulation/components/engines/test_asset_management_engine.py::test_invest_automation_max_cap PASSED [ 40%]
tests/simulation/components/engines/test_asset_management_engine.py::test_invest_capex_success PASSED [ 60%]
tests/simulation/components/engines/test_asset_management_engine.py::test_invest_negative_amount PASSED [ 80%]
tests/simulation/components/engines/test_asset_management_engine.py::test_invest_unknown_type PASSED [100%]

============================== 5 passed in 0.27s ===============================
```

### 2. Verification Script (`verify_firm.py`)
Confirmed that the refactored `Firm` class instantiates correctly and delegates calls as expected.

```
INFO:Verification:Firm instantiated successfully.
INFO:Verification:Inventory delegation working.
INFO:Verification:Initial inventory working.
INFO:Verification:Financial delegation working.
INFO:Verification:Verification passed.
```

## Tech Debt Note
- **Legacy Attributes**: While `Firm` no longer stores `_wallet` or `_inventory` directly, some external inspectors or tests might still try to access these private attributes. We have mitigated this by exposing properties (e.g., `wallet`), but direct access to `_inventory` will fail if not updated to use `inventory_component.main_inventory`.
- **Mocking**: Future tests must mock `IFirmComponent` protocols rather than the `Firm` class directly when testing engines, to ensure decoupling is maintained.
