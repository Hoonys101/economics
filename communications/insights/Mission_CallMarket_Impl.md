# Mission Insight: Inter-bank Call Market Implementation

**Mission Key**: CallMarket_Impl
**Date**: 2024-05-22
**Author**: Jules

## 1. Technical Debt & Architecture

### Settlement System Supremacy
The implementation strictly adheres to the "Sacred Sequence" by delegating all financial transfers to the `SettlementSystem`. The `CallMarketService` acts purely as a matching engine and settlement orchestrator. It never directly modifies agent balances.
- **Risk**: The `SettlementSystem` is a critical dependency. Any failure in `transfer` (e.g., due to race conditions or locked wallets) directly impacts market clearing.
- **Handling**: Failed settlements during clearing currently result in the match being skipped/discarded to preserve market flow.

### Config Consistency (TICKS_PER_YEAR)
Interest calculations rely heavily on `TICKS_PER_YEAR`.
- **Observation**: Codebase grep showed variations in `TICKS_PER_YEAR` (100 vs 360) in different contexts/tests.
- **Resolution**: `CallMarketService` accepts `config_module` in its constructor to dynamically load this value, defaulting to 100. This dependency must be managed carefully to ensure the injected config matches the simulation's time scale.

### Agent Resolution
The service bridges the gap between DTOs (using `int` IDs) and the `SettlementSystem` (using `Agent` objects) via `IAgentRegistry`.
- **Constraint**: This assumes all participants (Banks) are registered and retrievable via `IAgentRegistry`.

## 2. API Evolution

### Robust Time Handling
During code review, it was identified that relying on `agent_registry._state.tick` was a violation of encapsulation and created a fragile dependency on private state.
- **Change**: The `ICallMarket` interface was updated (`api.py`) so that `clear_market(tick)` and `settle_matured_loans(tick)` accept the current simulation tick explicitly.
- **Benefit**: This makes the service stateless with respect to time and easier to test, as well as decoupling it from `SimulationState` internals.

## 3. Future Considerations

### Reserve Accounts
Currently, "reserves" are treated as synonymous with the agent's main wallet balance in `DEFAULT_CURRENCY`.
- **Future Work**: If a distinction between "Vault Cash" and "Central Bank Reserves" is introduced (Phase 5+), the `submit_loan_offer` validation and `SettlementSystem` calls will need to target the specific reserve account/component.

### Default Handling
Matured loans that fail to settle (e.g., borrower has insufficient funds) currently log an error but remain in the `active_loans` map.
- **Recommendation**: Implement a dedicated `Default` state or `DistressHandler` to manage bad debt, potentially triggering a liquidation or bailout protocol.

### Async/Saga Pattern
The current `clear_market` is synchronous. If settlement becomes an async Saga (as seen in Housing), this service will need to be refactored to handle `PENDING` states and callbacks.
