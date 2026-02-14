# Technical Debt Ledger (TECH_DEBT_LEDGER.md)

| ID | Module / Component | Description | Priority / Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TD-ARCH-SEC-GOD** | System | **Auth Missing**: God-Mode WebSocket commands (`GodCommandDTO`) lack authentication/tokens. | **High**: Security Risk. | Identified |
| **TD-INT-PENNIES-FRAGILITY** | System | **Penny-Float Duality**: Widespread `hasattr`/`getattr` for `xxx_pennies` vs `xxx`. Needs Unified API. | **High**: Logic Inconsistency. | Identified |
| **TD-INT-STRESS-SCALE** | System | **O(N) Stress Scan**: Bank -> Depositor reverse index implemented. | **Low** | ✅ Resolved |
| **TD-INT-WS-SYNC** | System | **WS Polling**: Event-driven broadcast via TelemetryExchange implemented. | **Low** | ✅ Resolved |
| **TD-ARCH-PROTO-LOCATION** | System | **Bleeding Protocols**: Refactored to `modules/api/protocols.py`. | **Low** | ✅ Resolved |
| **TD-INT-BANK-ROLLBACK** | Finance | **Rollback Coupling**: Bank rollback logic dependent on `hasattr` implementation details. | **Low**: Abstraction Leak. | Identified |
| **TD-DATA-01-MOCK** | Finance | **Protocol/Mock Drift**: `ISettlementSystem` lacks `audit_total_m2`. Manual mocking in tests. | **High**: Regression Risk. | Open |
| **TD-STR-GOD-DECOMP** | Architecture | **Residual God Classes**: `Firm` (1276 lines) and `Household` (1042 lines) exceed 800-line limit. | **Medium**: Maintenance friction. | Open |
| **TD-ARCH-DI-SETTLE** | Architecture | **DI Timing**: `AgentRegistry` injection into `SettlementSystem` happens post-initialization. | **Low**: Initialization fragility. | Open |
| **TD-UI-DTO-PURITY** | Cockpit | **Manual Deserialization**: UI uses raw dicts/manual mapping for Telemetry. Needs `pydantic`. | **Medium**: Code Quality. | Open |
| **TD-GHOST-CONSTANTS** | System | **Registry Binding**: `from config import PARAM` refactored to `import config`. | **Low** | Resolved |
| **TD-UI-WS-PROD** | Cockpit | **WS Server Wiring**: Real simulation loop wired via `Bridge` pattern in Phase 4. | **Low** | Resolved |
| **TD-COCKPIT-FE** | Simulation | **Cockpit Ready**: Scaffold, Visualizers, and Dynamic Controls (UI-02) fully merged. | **Low** | Resolved |
| **TD-CRIT-FLOAT-SETTLE** | Settlement | **Critical Float Leak**: Float passed to int-only settlement. | **Critical**: Crash. | Open |
| **TD-DATA-03-PERF** | Performance | **Phase 8 Performance Risk**: O(N) iteration in `DemographicManager`. | **High**: Performance. | Open |
| **TD-SYS-BATCH-FRAGILITY** | Architecture | **Manifest Persistence**: Regex-based editing is brittle. | **High**: Stability. | Open |
| **TD-MON-SETTLEMENT-DRIFT** | Protocol | **Protocol Drift**: `ISettlementSystem` missing `mint_and_distribute`. | **Medium**: Architecture. | Open |
| **TD-SYS-GHOST-CONSTANTS** | Architecture | **Config Imports**: `from config import` bypasses Registry hot-swapping. | **Medium**: Flexibility. | Open |

---
> [!NOTE]
> ✅ **Resolved Debt History**: For clarity, all resolved technical debt items and historical lessons have been moved to [TECH_DEBT_HISTORY.md](./TECH_DEBT_HISTORY.md).

---

## 📓 Implementation Lessons & Detailed Debt (Open)


---
### ID: TD-CRIT-FLOAT-SETTLE
### Title: Critical Float Leak in Settlement (Startup/Emergency)
- **Symptom**: `SETTLEMENT_TYPE_ERROR` during `Startup Capital` and `emergency_buy`. Logs show `Amount must be int, got <class 'float'>`.
- **Risk**: **Simulation Crash**. The economy cannot initialize or trade basic goods.
- **Solution**: Enforce strict `int()` casting in `Firm.initialize` and `Household.consume` before invoking settlement.

---

### ID: TD-ARCH-SEC-GOD
### Title: God-Mode Command Authentication (Zero-Security Cockpit)
- **Symptom**: WebSocket server accepts `GodCommandDTO` without any token verification or source validation.
- **Risk**: External manipulation if server is exposed (0.0.0.0 binding).
- **Solution**: Implement `GOD_MODE_TOKEN` header validation and restricted IP binding.

---
### ID: TD-INT-PENNIES-FRAGILITY
### Title: Integer Pennies Compatibility Debt
- **Symptom**: Integration logic heavily uses `hasattr(agent, 'xxx_pennies')` to bridge between new Penny-system and legacy Float-system DTOs.
- **Risk**: Static type analysis (`mypy`) failures and runtime fragility.
- **Solution**: Finalize Penny migration for ALL telemetry DTOs and remove `hasattr` wrappers.

---
### ID: TD-INT-STRESS-SCALE
### Title: O(N) Complexity in Bank Stress Scenarios
- **Symptom**: `FORCE_WITHDRAW_ALL` iterates the entire `AgentRegistry` to find account holders for a specific bank.
- **Risk**: Linear slowdown as agent count scales ($O(Agents)$ per bank command).
- **Solution**: Implement a reverse index `Bank -> List[Depositors]` in the `SettlementSystem`.

---
### ID: TD-INT-WS-SYNC
### Title: Loosely Coupled WebSocket Polling (10Hz Polling)
- **Symptom**: `SimulationServer` broadcasts telemetry using a fixed `asyncio.sleep(0.1)` interval regardless of engine tick speed.
    - **Risk**: Telemetry lag or unnecessary CPU cycles.
    - **Solution**: Implement event-driven triggers where the Engine (Phase 8) notifies the Server thread to broadcast immediately after tick completion.

---
### ID: TD-DATA-03-PERF
### Title: Phase 8 Performance Risk (Demographics)
- **Symptom**: `DemographicManager` iterates all households ($O(N)$) every tick to calculate gender statistics.
- **Risk**: Simulation slowdown as agent count scales > 10,000.
- **Solution**: Implement incremental caching where stats are updated only on agent birth/death events.

---
### ID: TD-SYS-BATCH-FRAGILITY
### Title: Brittle Manifest Persistence
- **Symptom**: `command_manifest.py` is edited via Regex pattern matching, which is prone to corruption if formatting changes.
- **Risk**: Loss of mission data or syntax errors in vital registry files.
- **Solution**: Migrate manifest storage to a structured format (JSON/SQLite) or use AST-based editing.

---
### ID: TD-MON-SETTLEMENT-DRIFT
### Title: Settlement Protocol Drift
- **Symptom**: `CommandService` relies on `mint_and_distribute`, but `ISettlementSystem` interface does not define it.
- **Risk**: Runtime errors if the concrete implementation changes or if mocks are not updated.
- **Solution**: Formalize `mint_and_distribute` in the `ISettlementSystem` protocol definition.

---
### ID: TD-SYS-GHOST-CONSTANTS
### Title: Ghost Constants (Config Imports)
- **Symptom**: Modules use `from config import PARAM`, binding values at import time.
- **Risk**: `GlobalRegistry` updates (e.g., God Mode parameter tweaks) are ignored by these modules.
- **Solution**: Refactor all config access to use `config.PARAM` or `GlobalRegistry.get_param()`.
