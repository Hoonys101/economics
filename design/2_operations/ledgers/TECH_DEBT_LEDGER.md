# Technical Debt Ledger (TECH_DEBT_LEDGER.md)

| ID | Module / Component | Description | Priority / Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TD-INT-PENNIES-FRAGILITY** | System | **Penny-Float Duality**: Widespread `hasattr`/`getattr` for `xxx_pennies` vs `xxx`. Needs Unified API. | **High**: Logic Inconsistency. | Identified |
| **TD-INT-BANK-ROLLBACK** | Finance | **Rollback Coupling**: Bank rollback logic dependent on `hasattr` implementation details. | **Low**: Abstraction Leak. | Identified |
| **TD-STR-GOD-DECOMP** | Architecture | **Residual God Classes**: `Firm` (1276 lines) and `Household` (1042 lines) exceed 800-line limit. | **Medium**: Maintenance friction. | Open |
| **TD-ARCH-DI-SETTLE** | Architecture | **DI Timing**: `AgentRegistry` injection into `SettlementSystem` happens post-initialization. | **Low**: Initialization fragility. | Open |
| **TD-UI-DTO-PURITY** | Cockpit | **Manual Deserialization**: UI uses raw dicts/manual mapping for Telemetry. Needs `pydantic`. | **Medium**: Code Quality. | Open |
| **TD-TEST-MOCK-DRIFT-GEN** | Testing | **Protocol-Mock Drift**: Manual Mocks (e.g., `MockBank`) frequently drift from their `Protocol` definitions. | **High**: CI Stability. | Mitigation: create_autospec |
| **TD-TEST-UNIT-SCALE** | Testing | **Unit Scale Ambiguity**: Mismatch between "Dollars" (Float) in tests and "Pennies" (Int) in Engines. | **High**: Financial Logic. | Mitigation: int(val * 100) |

---
> [!NOTE]
> ✅ **Resolved Debt History**: For clarity, all resolved technical debt items and historical lessons have been moved to [TECH_DEBT_HISTORY.md](./TECH_DEBT_HISTORY.md).

---

## 📓 Implementation Lessons & Detailed Debt (Open)


---
### ID: TD-INT-PENNIES-FRAGILITY
### Title: Integer Pennies Compatibility Debt
- **Symptom**: Integration logic heavily uses `hasattr(agent, 'xxx_pennies')` to bridge between new Penny-system and legacy Float-system DTOs.
- **Risk**: Static type analysis (`mypy`) failures and runtime fragility.
- **Solution**: Finalize Penny migration for ALL telemetry DTOs and remove `hasattr` wrappers.


---
### ID: TD-TEST-MOCK-DRIFT-GEN
### Title: Recursive Protocol Drift in Mocks
- **Symptom**: `TypeError` when instantiating abstract Mocks.
- **Root Cause**: `Protocol` or `Interface` adds methods, but manual `Mock` implementations in `tests/` are not updated.
- **Solution**: Use `unittest.mock.create_autospec(Interface)` or enforce a shared `MockRegistry` that is audited automatically.

---
### ID: TD-TEST-UNIT-SCALE
### Title: Dollar-Penny Unit Confusion in Tests
- **Symptom**: Magnitude errors in assertions (e.g., `expected 1.0` vs `actual 0.01`).
- **Root Cause**: Testing layer uses "Dollars" (Logical) but Engine layer uses "Pennies" (Physical Integers).
- **Solution**: Adopt strict naming convention `amount_pennies` in tests or use a `to_pennies()` helper for all fixture definitions.
