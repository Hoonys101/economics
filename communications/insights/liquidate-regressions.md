# Insight Report: Liquidate Regressions

## 1. Architectural Insights

### Technical Debt Identified

1.  **Protocol Drift in Housing Market**:
    The `HousingTransactionHandler` was relying on a mix of `isinstance` checks and implicit assumptions about agent capabilities (e.g., `current_wage`). This violated the **Protocol Purity** guardrail. We are introducing `IHousingTransactionParticipant` to explicitly define the requirements for buyers.

2.  **Implicit Context Passing**:
    The handler was accessing global or semi-global configuration states (e.g., `context.config_module`). We are introducing `HousingTransactionContextDTO` (implicitly via strict typed arguments or a dedicated context object) to decouple the handler from the monolithic simulation state.

3.  **Firm Inventory Logic Separation**:
    The `Firm` class was acting as a God Class. By delegating inventory management to `InventoryComponent` and ensuring it handles `InventorySlot` logic correctly, we enforce **Logic Separation**. The `Firm` class now acts as an orchestrator rather than implementing low-level storage logic.

### Architectural Decisions

1.  **Strict DTOs for Market API**:
    We are enforcing strict DTO usage (`MarketConfigDTO`, `HousingTransactionContextDTO`) in `modules/market/api.py` to define clear boundaries between the Market domain and other systems.

2.  **Zero-Sum Enforcement in Handlers**:
    The `HousingTransactionHandler` is being refactored to use a strict Saga pattern with compensation steps to ensure **Zero-Sum Integrity**. Every financial transfer must be balanced, and failures at any stage must trigger precise reversals.

## 2. Test Evidence

### Firm Inventory Slots

```
tests/test_firm_inventory_slots.py::test_add_item_main_slot PASSED       [ 12%]
tests/test_firm_inventory_slots.py::test_add_item_input_slot PASSED      [ 25%]
tests/test_firm_inventory_slots.py::test_quality_averaging_main PASSED   [ 37%]
tests/test_firm_inventory_slots.py::test_quality_averaging_input PASSED  [ 50%]
tests/test_firm_inventory_slots.py::test_remove_item_input PASSED        [ 62%]
tests/test_firm_inventory_slots.py::test_remove_item_input_insufficient PASSED [ 75%]
tests/test_firm_inventory_slots.py::test_clear_inventory PASSED          [ 87%]
tests/test_firm_inventory_slots.py::test_facade_property PASSED          [100%]
```

### Housing Transaction Handler

```
tests/unit/markets/test_housing_transaction_handler.py::test_housing_transaction_success PASSED
tests/unit/markets/test_housing_transaction_handler.py::test_housing_transaction_insufficient_down_payment PASSED
tests/unit/markets/test_housing_transaction_handler.py::test_housing_transaction_loan_rejected PASSED
tests/unit/markets/test_housing_transaction_handler.py::test_housing_transaction_disbursement_failed PASSED
```
