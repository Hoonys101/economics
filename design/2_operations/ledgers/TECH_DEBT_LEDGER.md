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
| **TD-CRIT-FLOAT-CORE** | Finance | **Float Core**: `SettlementSystem` and `MatchingEngine` use `float` instead of `int` pennies. | **Critical**: Determinism. | **Identified** |
| **TD-RUNTIME-TX-HANDLER** | Transaction | **Missing Handler**: `bond_interest` tx type not registered in `TransactionExecutor`. | **High**: Runtime Failure. | **Identified** |
| **TD-RUNTIME-DEST-MISS** | Lifecycle | **Ghost Destination**: Transactions failing with "Destination account does not exist: 120". | **High**: Runtime Failure. | **Identified** |
| **TD-TEST-MOCK-STALE** | Testing | **Stale Mocks**: `WorldState` mocks used deprecated `system_command_queue`. | **High**: Test Blindness. | **Resolved** |
| **TD-ARCH-GOV-MISMATCH** | Architecture | **Singleton vs List**: `WorldState` has `governments` (List) but `TickOrchestrator` uses `government` (Singleton). | **Medium**: Logic Fragility. | **Identified** |

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
### ID: TD-ARCH-GOV-MISMATCH
### Title: Government Structure Mismatch (Singleton vs List)
- **Symptom**: `WorldState` definitions use `self.governments: List[Government]`, but `TickOrchestrator` and `Simulation` initialization often treat it as a singleton `self.government`.
- **Risk**: Semantic confusion and potential runtime errors if multiple governments are ever introduced. Accessing `state.government` relies on dynamic attribute injection or backward compatibility properties not explicitly defined in the type hint.
- **Solution**: Standardize on `governments` (List) or explicit `primary_government` property.
