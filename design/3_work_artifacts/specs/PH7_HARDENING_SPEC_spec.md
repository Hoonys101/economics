# Design Spec: PH7 Hardening (TD-271 & TD-272)

## 1. Introduction
This document specifies the architectural reforms needed to address two critical technical debts in Phase 7:
- **TD-271**: `OrderBookMarket` Interface Compliance.
- **TD-272**: `PersistenceManager` Domain Purity Reform.

## 2. TD-271: OrderBookMarket Interface Compliance

### 2.1 Problem
`OrderBookMarket` exposes internal `MarketOrder` objects through `buy_orders` and `sell_orders` properties, violating the `IMarket` protocol which expects `Order` DTOs.

### 2.2 Solution
- Rename internal dictionaries to `_buy_orders` and `_sell_orders`.
- Implement `@property` getters that convert internal `MarketOrder` instances to public `Order` DTOs on-the-fly.
- Ensure `modules/market/api.py` correctly defines `IMarket`.

## 3. TD-272: PersistenceManager Domain Purity Reform

### 3.1 Problem
`PersistenceManager` is a "God Class" that aggregates data by directly inspecting agent internals, causing tight coupling and violating SRP.

### 3.2 Solution
- **Decoupling**: Move data aggregation logic out of `PersistenceManager`.
- **DTO-Driven**: refactor `PersistenceManager.buffer_data` to receive pre-assembled DTOs (`AgentStateData`, `TransactionData`, `EconomicIndicatorData`).
- **Orchestration**: The `Engine` or a dedicated `AnalyticsSystem` should perform the aggregation and pass the DTOs to the persistence layer.
- **Agent Integration**: Utilize `agent.get_state_dto()` (Firm) and `agent.create_snapshot_dto()` (Household) to gather data safely.

## 4. 🚨 Risk & Impact Audit
- **High Test Impact**: Existing tests for `PersistenceManager` and `OrderBookMarket` will require significant updates to align with the new DTO-based interfaces.
- **Polymorphism**: Restores the ability to treat all markets as `IMarket` consistently.
- **Purity**: Prevents domain logic leaks into the persistence system.

## 5. Verification Plan
- **Zero Leakage**: `trace_leak.py` must maintain 0.0000% error.
- **Inventory Purity**: `audit_inventory_access.py` must show 0 direct `.inventory` violations.
- **Integration Tests**: `pytest tests/integration/test_persistence_purity.py` (New test required).

## 6. 🚨 Mandatory Reporting
All implementation findings and newly discovered debt must be recorded in `communications/insights/ARCH_HARDENING_PH7.md`.
