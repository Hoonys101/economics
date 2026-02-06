# Spec: TD-256 Inventory Abstraction (Domain Purity)

## 1. Objective
Refactor the simulation engine to prevent direct mutation of agent inventory lists. All inventory changes must be delegated to a strict `IInventoryHandler` protocol to ensure transactional integrity and atomicity, especially during complex Sagas (e.g., Housing).

## 2. Rationale
Directly modifying `agent.inventory` (which is often a raw `list` or `dict`) bypasses the `SettlementSystem`'s oversight and risks:
- Race conditions during multi-party transfers.
- "Magic items" appearing without a transaction record.
- Inconsistent state during Saga rollbacks.

## 3. Proposed Architecture

### 3.1 IInventoryHandler Protocol [NEW]
Define a runtime-checkable protocol in `modules/simulation/api.py`.

```python
@runtime_checkable
class IInventoryHandler(Protocol):
    def add_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None) -> bool:
        """Atomically adds items to storage with optional logging."""
        ...

    def remove_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None) -> bool:
        """Atomically removes items if available; returns False if insufficient."""
        ...

    def get_quantity(self, item_id: str) -> float:
        """Returns current quantity of a specific item."""
        ...
```

### 3.2 Implementation in Agents
Modify `modules/agents/firm.py` and `modules/agents/household.py` to:
1. Implement `IInventoryHandler`.
2. Encapsulate the raw `inventory` storage (make it protected: `_inventory`).
3. Redirect all production and sale logic to use the protocol methods.

## 4. Implementation Steps (Jules Mission)
1. **Define Protocol**: Add `IInventoryHandler` to `modules/simulation/api.py`.
2. **Update Firm**: Refactor `Firm.inventory` access in `modules/agents/firm.py`.
3. **Update Household**: Refactor `Household.inventory` access in `modules/agents/household.py`.
4. **Harden Settlement**: Update `SettlementSystem` to use `isinstance(agent, IInventoryHandler)` before attempting goods transfers.

## 5. Verification
- `pytest tests/unit/test_inventory_handler.py`: (New) Verify that direct list manipulation is no longer possible for callers.
- `python scripts/trace_leak.py`: Ensure no new leaks are introduced.
