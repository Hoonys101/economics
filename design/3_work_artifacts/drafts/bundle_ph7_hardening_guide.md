# Mission Guide: PH7 Architectural Hardening (TD-271, TD-272)

## 1. Objectives
- **TD-272**: Refactor `PersistenceManager` to use Agent DTOs/Snapshots.
- **TD-271**: Align `OrderBookMarket` with `IMarket` / `Market` contract.
- **TD-Cleanup**: Finalize ~60 remaining `.inventory` direct access violations.

## 2. Reference Context (MUST READ)
- **Spec**: [SPEC_DEBT_RECOVERY_PH7.md](file:///c:/coding/economics/design/3_work_artifacts/specs/SPEC_DEBT_RECOVERY_PH7.md)
- **Protocol**: `simulation/interfaces/market_interface.py` (`IMarket`)
- **Ledger**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`

## 3. Implementation Roadmap

### Phase 1: Persistence Purity (TD-272)
1. Modify `simulation/systems/persistence_manager.py`.
2. Update `buffer_tick_state` to call `agent.create_snapshot_dto()` (HH) and `agent.get_state_dto()` (Firm).
3. Update mapping logic to use DTO fields.

### Phase 2: Market Compliance (TD-271)
1. Modify `simulation/markets/order_book_market.py`.
2. Ensure `buy_orders` and `sell_orders` expose `Order` DTOs.
3. Verify signature compliance with `IMarket`.

### Phase 3: Inventory Cleanup
1. Audit and refactor direct `.inventory` access in `ma_manager.py`, `bootstrapper.py`, `persistence_manager.py`.
2. Use `IInventoryHandler` protocol ( `add_item`, `remove_item`, `get_quantity`).

## 4. Verification
- `python scripts/audit_inventory_access.py` (Must show 0 violations).
- `pytest tests/integration/test_inventory_purity.py`
- `python trace_leak.py` (Must show 0.0000% leak).
