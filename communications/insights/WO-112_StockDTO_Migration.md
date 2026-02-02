# Insight: Stock Market Migration to Immutable OrderDTO

## Context
The `StockMarket` previously relied on the mutable `StockOrder` class, which allowed in-place modification of order prices (for limit enforcement) and quantities (for partial fills). This pattern violated the system-wide move towards immutable Data Transfer Objects (DTOs), specifically `OrderDTO`.

## Architectural Decision: The ManagedOrder Wrapper
To reconcile the requirement for immutable external DTOs with the internal need for mutable state during order matching, we introduced the `ManagedOrder` pattern.

### The Problem
- **Immutability vs. Efficiency**: `OrderDTO` is frozen. However, efficient order matching often requires updating "remaining quantity" without allocating new objects for every partial fill.
- **Price Clamping**: The market enforces price limits (daily upper/lower bounds). Previously, this mutated the incoming order. With immutable DTOs, this requires creating a new DTO instance if the price is adjusted.

### The Solution
We introduced a private, internal wrapper class:

```python
@dataclass
class ManagedOrder:
    order: OrderDTO
    remaining_quantity: float
    created_tick: int
```

- **External Interface**: The public API (`place_order`, `match_orders`) accepts and returns pure `OrderDTO`s (or `Transaction`s derived from them).
- **Internal State**: The `StockMarket` internally stores `ManagedOrder` instances in its order books.
- **Mutation**:
    - **Quantity**: When a trade occurs, `ManagedOrder.remaining_quantity` is decremented. The `OrderDTO` inside remains untouched.
    - **Price**: If an incoming `OrderDTO` has a price outside the valid range, a *new* `OrderDTO` is created with the clamped price before being wrapped in `ManagedOrder`.

## Implications
1.  **Strict Boundary**: The `ManagedOrder` is never exposed outside the `StockMarket`. It is purely an implementation detail.
2.  **Testing Strategy**: Tests must now be "black-box", verifying state changes via public getters (`get_market_summary`) rather than inspecting internal order lists or expecting input objects to be mutated.
3.  **Schema Change**: All agents interacting with the stock market must now use `OrderDTO` with `item_id="stock_{firm_id}"` instead of `StockOrder`.

## Status
- **Resolved**: The conflict between immutable architecture and mutable market logic.
- **Pending**: Full deprecation of the `StockOrder` class in `simulation/models.py`.
