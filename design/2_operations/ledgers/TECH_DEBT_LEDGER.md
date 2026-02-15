# Technical Debt Ledger (TECH_DEBT_LEDGER.md)

| ID | Module / Component | Description | Priority / Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TD-ARCH-SEC-GOD** | System | **Auth Missing**: God-Mode WebSocket commands (`GodCommandDTO`) lack authentication/tokens. | **High**: Security Risk. | Identified |
| **TD-INT-PENNIES-FRAGILITY** | System | **Penny-Float Duality**: Widespread `hasattr`/`getattr` for `xxx_pennies` vs `xxx`. Needs Unified API. | **High**: Logic Inconsistency. | Identified |
| **TD-INT-BANK-ROLLBACK** | Finance | **Rollback Coupling**: Bank rollback logic dependent on `hasattr` implementation details. | **Low**: Abstraction Leak. | Identified |
| **TD-STR-GOD-DECOMP** | Architecture | **Residual God Classes**: `Firm` (1276 lines) and `Household` (1042 lines) exceed 800-line limit. | **Medium**: Maintenance friction. | Open |
| **TD-ARCH-DI-SETTLE** | Architecture | **DI Timing**: `AgentRegistry` injection into `SettlementSystem` happens post-initialization. | **Low**: Initialization fragility. | Open |
| **TD-UI-DTO-PURITY** | Cockpit | **Manual Deserialization**: UI uses raw dicts/manual mapping for Telemetry. Needs `pydantic`. | **Medium**: Code Quality. | Open |
| **TD-CRIT-FLOAT-SETTLE** | Settlement | **Critical Float Leak**: Float passed to int-only settlement. | **Critical**: Crash. | Open |

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
