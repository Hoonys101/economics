# Design Spec: Inventory Slot Protocol

## 1. Introduction & Goal

**Problem**: The `audit_inventory_purity_20260211.md` report identified a critical architectural inconsistency. While the main product inventory is managed via the `IInventoryHandler` interface, the raw material inventory (`input_inventory`) is mutated directly from multiple disparate locations (`GoodsTransactionHandler`, `Registry`, `Bootstrapper`, `Firm.produce`). This bypasses protocol, duplicates logic, and prevents consistent data integrity checks like quality averaging.

**Goal**: To refactor all inventory management to use a single, unified protocol. This will be achieved by extending the existing `IInventoryHandler` interface to support multiple inventory "slots," thereby centralizing access logic, eliminating code duplication, and ensuring consistent behavior for all inventory types.

## 2. Proposed Design: Extending `IInventoryHandler`

To avoid bloating the `Firm` class with another interface, we will expand the existing `IInventoryHandler` to be slot-aware.

### 2.1. `InventorySlot` Enum

A new enum will be created to define the distinct inventory types.

**File**: `modules/simulation/api.py`
```python
from enum import Enum, auto

class InventorySlot(Enum):
    """Defines distinct inventory categories within an agent."""
    MAIN = auto()      # Primary product inventory for sale
    INPUT = auto()     # Raw material inventory for production
```

### 2.2. Updated `IInventoryHandler` Interface

The interface methods will be updated to accept an `inventory_slot` parameter, defaulting to `MAIN` for backward compatibility.

**File**: `modules/simulation/api.py`
```python
class IInventoryHandler(ABC):
    """Interface for agents that can hold and manage an inventory of items."""

    @abstractmethod
    def add_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, quality: float = 1.0, slot: InventorySlot = InventorySlot.MAIN) -> bool:
        """Adds an item to a specific inventory slot."""
        ...

    @abstractmethod
    def remove_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, slot: InventorySlot = InventorySlot.MAIN) -> bool:
        """Removes an item from a specific inventory slot."""
        ...

    @abstractmethod
    def get_quantity(self, item_id: str, slot: InventorySlot = InventorySlot.MAIN) -> float:
        """Gets the quantity of an item in a specific inventory slot."""
        ...

    @abstractmethod
    def get_quality(self, item_id: str, slot: InventorySlot = InventorySlot.MAIN) -> float:
        """Gets the average quality of an item in a specific inventory slot."""
        ...

    @abstractmethod
    def get_all_items(self, slot: InventorySlot = InventorySlot.MAIN) -> Dict[str, float]:
        """Returns a copy of all items in a specific inventory slot."""
        ...

    @abstractmethod
    def clear_inventory(self, slot: InventorySlot = InventorySlot.MAIN) -> None:
        """Clears all items from a specific inventory slot."""
        ...
```

## 3. Implementation Plan (`Firm` class)

### 3.1. State Management

- The `Firm` class will encapsulate both inventory dictionaries directly.
- The `production_state.input_inventory` dictionary will be removed. The state will now be stored in `Firm._input_inventory`.
- The `Firm.input_inventory` property will be refactored to use the new handler method.

**File**: `simulation/firms.py` (Pseudo-code)
```python
class Firm(..., IInventoryHandler, ...):
    def __init__(self, ...):
        # ...
        self._inventory: Dict[str, float] = {} # Existing MAIN inventory
        self._input_inventory: Dict[str, float] = {} # New INPUT inventory

        # Quality tracking for input inventory must also be added
        self._input_inventory_quality: Dict[str, float] = {}

        # The 'input_inventory' property on ProductionState is now obsolete.
        # self.production_state.input_inventory = {} -> REMOVE THIS

    @property
    def input_inventory(self) -> Dict[str, float]:
        """Facade property for backward compatibility during transition."""
        return self.get_all_items(slot=InventorySlot.INPUT)

    # ... implementation of all IInventoryHandler methods ...
```

### 3.2. Unified Logic Implementation

The `IInventoryHandler` methods will delegate to the correct internal dictionary based on the `slot` parameter. The quality averaging logic from `_add_inventory_internal` will be reused for both slots.

**File**: `simulation/firms.py` (Pseudo-code for `add_item`)
```python
    @override
    def add_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, quality: float = 1.0, slot: InventorySlot = InventorySlot.MAIN) -> bool:
        if slot == InventorySlot.MAIN:
            inventory_ref = self._inventory
            quality_ref = self.inventory_quality # production_state.inventory_quality
        elif slot == InventorySlot.INPUT:
            inventory_ref = self._input_inventory
            quality_ref = self._input_inventory_quality
        else:
            return False

        # Reuse existing quality averaging logic
        current_inventory = inventory_ref.get(item_id, 0.0)
        current_quality = quality_ref.get(item_id, 1.0)

        total_qty = current_inventory + quantity
        if total_qty > 0:
            new_avg_quality = ((current_inventory * current_quality) + (quantity * quality)) / total_qty
            quality_ref[item_id] = new_avg_quality

        inventory_ref[item_id] = total_qty
        return True
```
*(Note: `remove_item`, `get_quantity`, etc. will be implemented with similar slot-based branching.)*

## 4. Refactoring Targets

The following locations must be refactored to use the new slot-based handler.

1.  **`simulation/systems/handlers/goods_handler.py`**
    -   **Location**: `_apply_goods_effects` method, lines `~L113-114`.
    -   **Action**: Replace direct mutation with a protocol call.
    -   **Before**:
        ```python
        if is_raw_material and isinstance(buyer, Firm):
            buyer.input_inventory[tx.item_id] = buyer.input_inventory.get(tx.item_id, 0.0) + tx.quantity
        elif isinstance(buyer, IInventoryHandler):
            buyer.add_item(tx.item_id, tx.quantity, quality=tx_quality)
        ```
    -   **After**:
        ```python
        if isinstance(buyer, IInventoryHandler):
            slot = InventorySlot.INPUT if is_raw_material and isinstance(buyer, Firm) else InventorySlot.MAIN
            buyer.add_item(tx.item_id, tx.quantity, quality=tx_quality, slot=slot)
        else:
            logger.warning(f"GOODS_HANDLER_WARN | Buyer {buyer.id} does not implement IInventoryHandler")
        ```

2.  **`simulation/systems/registry.py`**
    -   **Location**: `_handle_goods_registry` method, lines `~L142-143`.
    -   **Action**: **DELETE** the redundant logic block. `GoodsTransactionHandler` is the sole authority.
    -   **Code to Delete**:
        ```python
        if is_raw_material and isinstance(buyer, Firm):
            buyer.input_inventory[tx.item_id] = buyer.input_inventory.get(tx.item_id, 0.0) + tx.quantity
        ```

3.  **`simulation/firms.py`**
    -   **Location**: `produce` method, lines `~L830-832`.
    -   **Action**: Replace direct mutation with a protocol call.
    -   **Before**:
        ```python
        for mat, amount in result.inputs_consumed.items():
            current_input = self.production_state.input_inventory.get(mat, 0.0)
            self.production_state.input_inventory[mat] = max(0.0, current_input - amount)
        ```
    -   **After**:
        ```python
        for mat, amount in result.inputs_consumed.items():
            self.remove_item(mat, amount, slot=InventorySlot.INPUT)
        ```

4.  **`simulation/bootstrapper.py`**
    -   **Location**: `L84-86` (approx).
    -   **Action**: Replace direct injection with a protocol call.
    -   **Before**: `firm.input_inventory[mat] = needed`
    -   **After**: `firm.add_item(mat, needed, slot=InventorySlot.INPUT)`

5.  **`simulation/systems/handlers/public_manager_handler.py`**
    -   **Action**: Apply the same refactoring as in `GoodsTransactionHandler`.

## 5. Verification & Testing Strategy

**High Risk**: This refactoring will break any test that directly accesses or modifies `firm.input_inventory`. A careful migration is required.

-   **Step 1: Code Search**: Perform a project-wide search for any usage of `.input_inventory`.
-   **Step 2: Test Migration**:
    -   All direct assignments (e.g., `firm.input_inventory['wood'] = 100`) in test setup files (`conftest.py` or individual tests) **MUST** be replaced with `firm.add_item('wood', 100, slot=InventorySlot.INPUT)`.
    -   All assertions (e.g., `assert firm.input_inventory['wood'] == 50`) **MUST** be replaced with `assert firm.get_quantity('wood', slot=InventorySlot.INPUT) == 50`.
-   **Step 3: New Tests**:
    -   Create a new test file (`tests/test_firm_inventory_slots.py`).
    -   Add tests to verify that `add_item` with `slot=InventorySlot.INPUT` correctly applies quality-averaging logic to the input inventory.
    -   Add tests to verify that `add_item` with `slot=InventorySlot.MAIN` still functions as before.
    -   Verify that calling `remove_item` on one slot does not affect the other.
-   **Step 4: Integration Check**: Ensure the main simulation scenario tests still pass, confirming that production correctly consumes raw materials from the new inventory slot.

## 6. Risk & Impact Audit (Analysis of Pre-flight Check)

-   **Constraint: Duplicated Logic in `GoodsTransactionHandler` and `Registry`**
    -   **Observation**: Both modules mutate `input_inventory`.
    -   **Mitigation**: This specification designates `GoodsTransactionHandler` as the sole authority and mandates the **deletion** of the corresponding code block in `Registry`, resolving the SRP violation.

-   **Constraint: The `Firm` God Class**
    -   **Observation**: `Firm` implements too many interfaces.
    -   **Mitigation**: This spec follows the recommendation to extend the existing `IInventoryHandler` with slots, rather than adding a new `IRawMaterialHandler` interface. This prevents further expansion of the `Firm` class's direct API surface.

-   **Risk: Widespread Test Breakage**
    -   **Observation**: Direct access to `firm.input_inventory` in tests will fail.
    -   **Mitigation**: Section 5 provides a clear, mandatory testing migration strategy, instructing developers on how to replace direct dictionary access with the new protocol methods.

-   **Risk: Inconsistent Quality Tracking**
    -   **Observation**: Direct mutations for `input_inventory` bypass the quality-averaging logic applied to the main inventory.
    -   **Mitigation**: Section 3.2 mandates that the refactored `add_item` method **must** apply the exact same quality-averaging logic to the `INPUT` slot as is used for the `MAIN` slot, ensuring data integrity as per `FINANCIAL_INTEGRITY.md`.

## 7. Mandatory Reporting Verification

All insights, observations, and potential technical debt discovered during the implementation of this specification will be logged in a new file under `communications/insights/refactor_inventory_protocol.md`. The completion of this task is contingent on the creation and submission of this report.
