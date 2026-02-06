# SPEC-TD-272: Persistence Manager Purity Reform

## 1. Problem Statement
The `PersistenceManager` currently violates domain purity by accessing internal agent properties directly (e.g., `agent.id`, `agent.assets`, `agent.is_employed`). This creates tight coupling and bypasses established DTO protocols.

## 2. Proposed Changes
Refactor `PersistenceManager.buffer_tick_state` in `simulation/systems/persistence_manager.py`:
- For `Household` agents: Use `agent.create_snapshot_dto()` (returns `HouseholdSnapshotDTO`).
- For `Firm` agents: Use `agent.get_state_dto()` (returns `FirmStateDTO`).
- Map these DTO fields to the `AgentStateData` buffer.

## 3. Benefits
- Enforces Separation of Concerns (SoC).
- Ensures the persistence layer only sees public data snapshots.
- Simplifies testing and mock injection.

---

# SPEC-TD-271: OrderBook IMarket Contract Compliance

## 1. Problem Statement
`OrderBookMarket` violates the `IMarket` protocol by using internal `MarketOrder` objects in its `buy_orders` and `sell_orders` dictionaries. `IMarket` (and the `Market` base class) requires these to be lists of `Order` DTOs.

## 2. Proposed Changes
Refactor `OrderBookMarket` in `simulation/markets/order_book_market.py`:
- **Option A (Preferred)**: Store `Order` DTOs directly and handle any mutability needed for matching in a separate internal tracking structure if necessary.
- **Option B**: Keep `MarketOrder` for internal matching logic but override `buy_orders` and `sell_orders` properties to return lists of `Order` DTOs to the outside world.
- Ensure all calls to `buy_orders` and `sell_orders` from outside the class receive `Order` DTOs.

## 3. Benefits
- Restores polymorphism across all market types.
- Ensures agents and observers interact with a stable, DTO-based interface.
