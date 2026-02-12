# Implementation: Inventory Slot Protocol

## Overview
This refactor introduced `InventorySlot` Enum and updated `IInventoryHandler` Protocol to support `MAIN` and `INPUT` inventory slots. This resolved logic duplication and established a clear distinction between product inventory and raw materials in `Firm` agents.

## Key Changes
1.  **Protocol Update**: `IInventoryHandler` methods now accept a `slot` parameter.
2.  **Firm Refactor**: `Firm` class now encapsulates `_input_inventory` and `_input_inventory_quality` directly, implementing the slot-aware protocol. The `input_inventory` property was retained as a read-only facade for backward compatibility during transition.
3.  **State Model Cleanup**: `ProductionState.input_inventory` was removed. `FirmSnapshotDTO` and `FirmStateDTO` now source input inventory from `Firm._input_inventory`.
4.  **System Cleanup**: `Registry` logic for physical goods inventory update was removed to eliminate double-counting, designating `GoodsTransactionHandler` as the sole authority.
5.  **Test Migration**: Direct access to `firm.input_inventory` (setter) was migrated to `firm.add_item(..., slot=InventorySlot.INPUT)` in tests.

## Insights & Observations
*   **Legacy Facades**: Retaining `input_inventory` property on `Firm` as a read-only facade (returning a copy) was crucial for maintaining API compatibility where `input_inventory` was read, while forcing migration for write operations.
*   **Test Mocking Patterns**: Tests mocking `Firm` often set arbitrary attributes. Migrating these required distinguishing between "Mock as State DTO" and "Mock as Agent". `FirmStateDTO` still has `production.input_inventory` which is valid, while `Firm` agent tests needed updates to use the protocol.
*   **Registry Redundancy**: The `Registry` was performing redundant inventory updates for physical goods, which was a potential source of bugs (double counting) if not for the fact that `GoodsTransactionHandler` and `Registry` usage was somewhat disjoint or overlapping. Centralizing this in the Handler is cleaner.

## Technical Debt
*   **AgentStateDTO**: `AgentStateDTO` currently only captures `inventory` (implied MAIN). It does not explicitly capture `input_inventory`. This means `save/load` mechanisms relying solely on `AgentStateDTO` might lose input inventory state for Firms. `Firm.get_current_state` and `load_state` were NOT updated to include input inventory in `AgentStateDTO` structure because `AgentStateDTO` definition was not scoped for change in this mission (it affects all agents). **Action Item**: Update `AgentStateDTO` to support multi-slot inventory or specific firm state persistence.
*   **ProductionStateDTO**: Still contains `input_inventory`. This is fine for DTOs but reflects the old structure where it was part of `ProductionState`. Ideally, `ProductionStateDTO` should perhaps be cleaner, but for now it serves as a transport for engine data.

## Verification
*   Added `tests/test_firm_inventory_slots.py` verifying slot isolation and quality averaging.
*   Migrated 5 integration test files.
*   Verified 132 tests passing.
