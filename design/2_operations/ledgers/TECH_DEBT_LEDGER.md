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

---
> [!NOTE]
> ✅ **Resolved Debt History**: For clarity, all resolved technical debt items and historical lessons have been moved to [TECH_DEBT_HISTORY.md](./TECH_DEBT_HISTORY.md).

---

## 📓 Implementation Lessons & Detailed Debt (Open)


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

