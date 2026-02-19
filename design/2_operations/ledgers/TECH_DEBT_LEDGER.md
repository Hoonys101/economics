# Technical Debt Ledger (TECH_DEBT_LEDGER.md)

| ID | Module / Component | Description | Priority / Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TD-CONF-GHOST-BIND** | Config | **Ghost Constants**: Modules bind config values at import time, preventing runtime hot-swap. | **Medium**: Dynamic Tuning. | **Identified** |
| **TD-TEST-TX-MOCK-LAG** | Testing | **Transaction Test Lag**: `test_transaction_engine.py` mocks are out of sync with `ITransactionParticipant` (overdraft support). | **Low**: Test Flakiness. | **Identified** |
| **TD-INT-BANK-ROLLBACK** | Finance | **Rollback Coupling**: Bank rollback logic dependent on `hasattr` implementation details. | **Low**: Abstraction Leak. | Open |
| **TD-ARCH-DI-SETTLE** | Architecture | **DI Timing**: `AgentRegistry` injection into `SettlementSystem` happens post-initialization. | **Low**: Initialization fragility. | Open |
| **TD-UI-DTO-PURITY** | Cockpit | **Manual Deserialization**: UI uses raw dicts/manual mapping for Telemetry. Needs `pydantic`. | **Medium**: Code Quality. | Open |
| **TD-PROC-TRANS-DUP** | Logic | **Handler Redundancy**: Logic overlap between legacy `TransactionManager` and new `TransactionProcessor`. | **Medium**: Maintenance. | **Resolved** |
| **TD-TRANS-INT-SCHEMA** | Transaction | **Schema Lag**: `Transaction` model (simulation/models.py) still uses `float` price. | **High**: Persistence Drift. | **Resolved** |
| **TD-DEPR-GOV-TAX** | Government | **Legacy API**: `Government.collect_tax` is deprecated. Use `settle_atomic`. | **Low**: Technical Debt. | **Resolved** |
| **TD-DEPR-FACTORY** | Factory | **Stale Path**: `agent_factory.HouseholdFactory` is stale. Use `household_factory`. | **Low**: Technical Debt. | **Resolved** |
| **TD-DEPR-STOCK-DTO** | Market | **Legacy DTO**: `StockOrder` is deprecated. Use `CanonicalOrderDTO`. | **Low**: Technical Debt. | Open |
| **TD-CRIT-FLOAT-CORE** | Finance | **Float Core**: `SettlementSystem` and `MatchingEngine` use `float` instead of `int` pennies. (Ongoing: M&A/StockMarket indices) | **Critical**: Determinism. | **Audit Done** |
| **TD-RUNTIME-TX-HANDLER** | Transaction | **Missing Handler**: `bailout`, `bond_issuance` tx types not registered. | **High**: Runtime Failure. | **Audit Done** |
| **TD-RUNTIME-DEST-MISS** | Lifecycle | **Ghost Destination**: Transactions failing for non-existent agents (Sequence error in `spawn_firm`). | **High**: Runtime Failure. | **Audit Done** |
| **TD-TEST-MOCK-STALE** | Testing | **Stale Mocks**: `WorldState` mocks used deprecated `system_command_queue`. | **High**: Test Blindness. | **Resolved** |
| **TD-ARCH-GOV-MISMATCH** | Architecture | **Singleton vs List**: `WorldState` has `governments` (List) vs Singelton `government`. | **Medium**: Logic Fragility. | **Identified** |
| **TD-GOV-SOLVENCY** | Government | **Binary Gates**: Spending modules use all-or-nothing logic; lack partial execution/solvency pre-checks. | **Medium**: Economic Stall. | **Audit Done** |
| **TD-CRIT-LIFECYCLE-ATOM** | Lifecycle | **Agent Startup Atomicity**: Firm registration (Registry) must occur *before* financial initialization (Transfer). | **Critical**: Runtime Crash. | Open |
| **TD-SYS-QUEUE-SCRUB** | Lifecycle | **Lifecycle Queue Scrubbing**: `AgentLifecycleManager` fails to remove stale IDs from `inter_tick_queue` and `effects_queue`. | **High**: Logic Leak. | Open |
| **TD-GOV-SPEND-GATE** | Government | **Binary Spending Gates**: Infrastructure/Welfare modules need "Partial Execution" support. | **High**: Economic Stall. | Open |
| **TD-CRIT-FLOAT-MA** | Finance | **M&A Float Violation**: `MAManager` and `StockMarket` calculate and transfer `float` values. | **Critical**: Type Error. | Open |
| **TD-RUNTIME-TX-HANDLER** | Transaction | **Missing Fiscal Handlers**: `bailout`, `bond_issuance` types not registered in `TransactionProcessor`. | **Medium**: Runtime Failure. | Open |
| **TD-PROTO-MONETARY** | Transaction | **Monetary Protocol Violation**: `MonetaryTransactionHandler` uses `hasattr` instead of Protocols. | **Low**: Logic Fragility. | Open |
| **TD-DX-AUTO-CRYSTAL** | DX / Ops | **Crystallization Overhead**: Manual Gemini Manifest registration required for session distillation. Needs "one-click" `session-go` integration. | **Medium**: DX Friction. | Open |
| **TD-LIFECYCLE-STALE** | Lifecycle | **Queue Pollution**: Missing scrubbing of `inter_tick_queue` after agent liquidation. | **Medium**: Determinism. | **Audit Done** |

---
> [!NOTE]
> ✅ **Resolved Debt History**: For clarity, all resolved technical debt items and historical lessons have been moved to [TECH_DEBT_HISTORY.md](./TECH_DEBT_HISTORY.md).

---

## 📓 Implementation Lessons & Detailed Debt (Open)

---
### ID: TD-CONF-GHOST-BIND
### Title: Ghost Constant Binding (Import Time)
- **Symptom**: `from config import MIN_WAGE` locks the value of `MIN_WAGE` at the moment of import.
- **Risk**: Changing the value in `GlobalRegistry` at runtime (e.g., God Mode) has no effect on modules that already imported the constant.
- **Solution**: Use a `ConfigProxy` or `DynamicConfig` object that resolves values at access time (`config.MIN_WAGE`).

---
### ID: TD-PROC-TRANS-DUP
### Title: Transaction Logic Duplication
- **Symptom**: Similar transaction processing logic exists in `TransactionManager` (Legacy) and `TransactionProcessor` (New).
- **Risk**: Fixes applied to one might not apply to the other, leading to divergent behavior.
- **Solution**: Deprecate `TransactionManager` and route all traffic through `TransactionProcessor`.

---
### ID: TD-GOV-SOLVENCY
### Title: Government Budget Guardrails (Binary Gates)
- **Symptom**: Infrastructure investment fails entirely if Treasury < 100% of requirement, even if 99% exists.
- **Risk**: Economic stagnation during minor fiscal deficits.
- **Solution**: Implement `PartialExecutionResultDTO` and `SolvencyException` with proactive balance checks via `SettlementSystem`.

---
### ID: TD-LIFECYCLE-STALE
### Title: Persistent Queue Pollution (Stale IDs)
- **Symptom**: Transactions for dead agents linger in `inter_tick_queue`.
- **Risk**: Ghost transactions attempts bloat logs and may trigger logic errors if IDs are reused.
- **Solution**: Implement a `ScrubbingPhase` in `AgentLifecycleManager` to purge invalid IDs from all queues.

---
### ID: TD-CRIT-FLOAT-CORE (M&A Expansion)
### Title: M&A and Stock Market Float Violation
- **Symptom**: `MAManager` passes `float` offer prices to `SettlementSystem.transfer`, causing `TypeError`.
- **Risk**: Runtime crash during hostile takeovers or mergers.
- **Solution**: Quantize all M&A valuations using `round_to_pennies()` before settlement boundary.
