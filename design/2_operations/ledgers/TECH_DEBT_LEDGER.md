# Technical Debt Ledger (TECH_DEBT_LEDGER.md)

| ID | Module / Component | Description | Priority / Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TD-INT-PENNIES-FRAGILITY** | System | **Penny-Float Duality**: Widespread `hasattr`/`getattr` for `xxx_pennies` vs `xxx`. Needs Unified API. | **High**: Logic Inconsistency. | Identified |
| **TD-INT-BANK-ROLLBACK** | Finance | **Rollback Coupling**: Bank rollback logic dependent on `hasattr` implementation details. | **Low**: Abstraction Leak. | Identified |
| **TD-STR-GOD-DECOMP** | Architecture | **Residual God Classes**: `Firm` (1276 lines) and `Household` (1042 lines) exceed 800-line limit. | **Medium**: Maintenance friction. | Open |
| **TD-ARCH-DI-SETTLE** | Architecture | **DI Timing**: `AgentRegistry` injection into `SettlementSystem` happens post-initialization. | **Low**: Initialization fragility. | Open |
| **TD-UI-DTO-PURITY** | Cockpit | **Manual Deserialization**: UI uses raw dicts/manual mapping for Telemetry. Needs `pydantic`. | **Medium**: Code Quality. | Open |
| **TD-TEST-LEGACY-SSOT** | Testing | **Stale Assertion**: `test_fiscal_integrity` asserts `agent.assets` instead of SSoT (`SettlementSystem`). | **High**: False Negative Risk. | Identified |
| **TD-TEST-MOCK-DRIFT** | Testing | **Protocol Mismatch**: `MockBank` misses abstract method `get_total_deposits`. | **High**: CI Failure. | Identified |

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
### ID: TD-TEST-LEGACY-SSOT
### Title: Legacy State Assertion in Fiscal Tests
- **Symptom**: `test_infrastructure_investment_generates_transactions_and_issues_bonds` fails asserting `gov.assets`.
- **Root Cause**: `FinanceSystem` updates `SettlementSystem` (SSoT) but legacy `agent.assets` attribute is not synchronized.
- **Solution**: Refactor test to assert against `settlement_system.get_balance(gov.id)`.

---
### ID: TD-TEST-MOCK-DRIFT
### Title: MockBank Protocol Verification Failure
- **Symptom**: `TypeError: Can't instantiate abstract class MockBank...` in `test_circular_imports_fix.py`.
- **Root Cause**: `IBank` interface added `get_total_deposits` but `MockBank` in tests was not updated to implement it.
- **Solution**: Implement `get_total_deposits` in `MockBank` (even if it returns 0).
