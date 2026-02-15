# Audit Report: Inventory Mutation Analysis

## Executive Summary
The analysis reveals a significant architectural inconsistency in inventory management. While the main product inventory (`_inventory`) is reasonably well-encapsulated within the `Firm` class's `IInventoryHandler` implementation, the raw material inventory (`input_inventory`) is subject to widespread, direct dictionary mutations from multiple external systems. This bypasses established protocols and introduces risks related to data integrity, code duplication, and maintainability.

## Detailed Analysis

### 1. Main Product Inventory (`_inventory`)
- **Status**: ✅ Implemented (Largely Correct)
- **Evidence**:
  - Mutations are primarily confined to methods within `simulation/firms.py` that implement the `IInventoryHandler` interface, such as `remove_item` (`firms.py:L646-651`), `clear_inventory` (`firms.py:L668-672`), and the internal helper `_add_inventory_internal` (`firms.py:L674-682`).
  - External systems correctly use the `IInventoryHandler` interface methods. For example, `Bootstrapper.inject_initial_liquidity` uses `firm.add_item()` (`bootstrapper.py:L90-92`).
- **Notes**: The `load_state` method (`firms.py:L268-271`) performs a direct mutation (`._inventory.clear()` and `._inventory.update()`). While a direct mutation, this is considered an acceptable exception for state hydration purposes.

### 2. Raw Material Inventory (`input_inventory`)
- **Status**: ❌ Missing Protocol Adherence
- **Evidence**: The `input_inventory` dictionary, belonging to `firm.production_state`, is directly modified by numerous external modules, violating the principle of using an interface for state changes.
- **Violation Points**:
  - **`simulation.bootstrapper.Bootstrapper`**: Directly injects raw materials at simulation start.
    - **Location**: `simulation/bootstrapper.py:L84-86`
    - **Code**: `firm.input_inventory[mat] = needed`
  - **`simulation.firms.Firm`**: The `produce` method directly consumes raw materials from `input_inventory` after a production run.
    - **Location**: `simulation/firms.py:L830-832`
    - **Code**: `self.production_state.input_inventory[mat] = max(0.0, current_input - amount)`
  - **`simulation.systems.handlers.goods_handler.GoodsTransactionHandler`**: Directly adds purchased raw materials to the buyer's inventory.
    - **Location**: `simulation/systems/handlers/goods_handler.py:L113-114`
    - **Code**: `buyer.input_inventory[tx.item_id] = buyer.input_inventory.get(tx.item_id, 0.0) + tx.quantity`
  - **`simulation.systems.handlers.public_manager_handler.PublicManagerTransactionHandler`**: Duplicates the direct mutation logic for goods sold by the Public Manager.
    - **Location**: `simulation/systems/handlers/public_manager_handler.py:L114-115`
    - **Code**: `buyer.input_inventory[tx.item_id] = buyer.input_inventory.get(tx.item_id, 0.0) + tx.quantity`
  - **`simulation.systems.registry.Registry`**: Contains seemingly redundant or legacy logic that also directly mutates `input_inventory`.
    - **Location**: `simulation/systems/registry.py:L142-143`
    - **Code**: `buyer.input_inventory[tx.item_id] = buyer.input_inventory.get(tx.item_id, 0.0) + tx.quantity`

## Risk Assessment
- **Data Integrity Leaks**: Direct mutations bypass any validation, logging, or quality-averaging logic present in the `IInventoryHandler` implementation (e.g., `_add_inventory_internal` in `firms.py`). This means raw materials do not benefit from quality tracking, which could lead to simulation inaccuracies.
- **Protocol Violation**: The `IInventoryHandler` interface is intended to govern these interactions. Ignoring it for `input_inventory` creates an inconsistent and confusing architecture, making the system harder to reason about and refactor.
- **Code Duplication**: The logic for adding raw materials is duplicated across `GoodsTransactionHandler`, `PublicManagerTransactionHandler`, and `Registry`. This is a classic maintenance hazard; a change in one place is likely to be missed in others, leading to bugs.

## Conclusion
The management of `input_inventory` is a significant architectural flaw. It completely bypasses the established `IInventoryHandler` protocol, leading to duplicated code and a high risk of data inconsistency. To align with the project's standards ([`FINANCIAL_INTEGRITY.md`](design/1_governance/architecture/standards/INDEX.md)), all manipulations of `input_inventory` should be refactored to use a standardized interface, similar to how `_inventory` is managed. This would centralize the logic, eliminate duplication, and allow for proper validation and tracking.
