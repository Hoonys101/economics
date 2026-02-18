# Technical Debt Ledger (TECH_DEBT_LEDGER.md)

| ID | Module / Component | Description | Priority / Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TD-MKT-FLOAT-MATCH** | Markets | **Market Precision Leak**: `MatchingEngine` uses `float` for price discovery. Violates Zero-Sum. | **Critical**: Financial Halo. | **Resolved** |
| **TD-ARCH-LIFE-GOD** | Systems | **God Manager**: `LifecycleManager` monolithically handles Birth, Death, Aging, Liquidation. | **Medium**: Coupling. | **Identified** |
| **TD-CONF-GHOST-BIND** | Config | **Ghost Constants**: Modules bind config values at import time, preventing runtime hot-swap. | **Medium**: Dynamic Tuning. | **Identified** |
| **TD-INT-PENNIES-FRAGILITY** | System | **Penny-Float Duality**: Widespread `hasattr`/`getattr` for `xxx_pennies` vs `xxx`. Needs Unified API. | **High**: Logic Inconsistency. | **Resolved** |
| **TD-TEST-TX-MOCK-LAG** | Testing | **Transaction Test Lag**: `test_transaction_engine.py` mocks are out of sync with `ITransactionParticipant` (overdraft support). | **Low**: Test Flakiness. | **Identified** |
| **TD-INT-BANK-ROLLBACK** | Finance | **Rollback Coupling**: Bank rollback logic dependent on `hasattr` implementation details. | **Low**: Abstraction Leak. | Open |
| **TD-ARCH-DI-SETTLE** | Architecture | **DI Timing**: `AgentRegistry` injection into `SettlementSystem` happens post-initialization. | **Low**: Initialization fragility. | Open |
| **TD-UI-DTO-PURITY** | Cockpit | **Manual Deserialization**: UI uses raw dicts/manual mapping for Telemetry. Needs `pydantic`. | **Medium**: Code Quality. | Open |
| **TD-PROC-TRANS-DUP** | Logic | **Handler Redundancy**: Logic overlap between legacy `TransactionManager` and new `TransactionProcessor`. | **Medium**: Maintenance. | **Identified** |
| **TD-CRIT-FLOAT-SETTLE** | Finance | **Float-to-Int Migration**: Residual `float` usage in `SettlementSystem` and `MatchingEngine`. | **Critical**: High Leakage risk. | **Identified** |
| **TD-DTO-DESYNC-2026** | DTO/API | **Contract Fracture**: `BorrowerProfileDTO` desync across Firm logic & tests. | **Critical**: System Integrity. | **Resolved** |
| **TD-TEST-SSOT-SYNC** | Testing | **SSoT Balance Mismatch**: Tests assert against legacy `.assets` attributes instead of `SettlementSystem`. | **High**: Verification Validity. | **Resolved** |
| **TD-TRANS-LEGACY-PRICING** | Transaction | **Float Cast Bridge**: `TransactionProcessor` converts integer `total_pennies` back to `float` for `SettlementResultDTO` compatibility. | **Medium**: Precision Risk. | **Identified** |

---
> [!NOTE]
> ✅ **Resolved Debt History**: For clarity, all resolved technical debt items and historical lessons have been moved to [TECH_DEBT_HISTORY.md](./TECH_DEBT_HISTORY.md).

---

## 📓 Implementation Lessons & Detailed Debt (Open)

---
### ID: TD-MKT-FLOAT-MATCH
### Title: Market Matching Engine Float Leakage
- **Symptom**: `MatchingEngine` calculates mid-prices and execution values using python `float`.
- **Risk**: Creates "Financial Dust" (micro-pennies) that accumulates over millions of transactions, breaking Zero-Sum audits.
- **Solution**: Refactor `MatchingEngine` to use Integer Math with explicit rounding rules (Round-Down / Remainder-to-Market-Maker).

---
### ID: TD-ARCH-LIFE-GOD
### Title: Lifecycle Manager Monolith
- **Symptom**: `LifecycleManager` class has grown to encapsulate Birth, Death, Aging, and Liquidation logic in a single file.
- **Risk**: Impossible to test isolation of "Death" logic without instantiating "Birth" dependencies. Violates SoC.
- **Solution**: Decompose into `BirthSystem`, `DeathSystem`, `AgingSystem` orchestrated by a lightweight Manager.

---
### ID: TD-CONF-GHOST-BIND
### Title: Ghost Constant Binding (Import Time)
- **Symptom**: `from config import MIN_WAGE` locks the value of `MIN_WAGE` at the moment of import.
- **Risk**: Changing the value in `GlobalRegistry` at runtime (e.g., God Mode) has no effect on modules that already imported the constant.
- **Solution**: Use a `ConfigProxy` or `DynamicConfig` object that resolves values at access time (`config.MIN_WAGE`).

---
### ID: TD-INT-PENNIES-FRAGILITY
### Title: Integer Pennies Compatibility Debt
- **Symptom**: Integration logic heavily uses `hasattr(agent, 'xxx_pennies')` to bridge between new Penny-system and legacy Float-system DTOs.
- **Risk**: Static type analysis (`mypy`) failures and runtime fragility.
- **Solution**: Finalize Penny migration for ALL telemetry DTOs and remove `hasattr` wrappers.

---
### ID: TD-PROC-TRANS-DUP
### Title: Transaction Logic Duplication
- **Symptom**: Similar transaction processing logic exists in `TransactionManager` (Legacy) and `TransactionProcessor` (New).
- **Risk**: Fixes applied to one might not apply to the other, leading to divergent behavior.
- **Solution**: Deprecate `TransactionManager` and route all traffic through `TransactionProcessor`.

---
### ID: TD-DTO-DESYNC-2026
### Title: Cross-Module DTO/API Contract Fracture
- **Symptom**: `TypeError` (unexpected keyword 'borrower_id') in Firm logic and `Subscriptable` error in tests following Dataclass migration.
- **Risk**: PR reviews pass based on local diffs but hidden global regressions persist. Systemic failure in loan assessments.
- **Solution**: 
    1. Liquidate current 27 failures.
    2. **Protocol Update**: Every Mission SPEC must include an "API/DTO Impact" section.
    3. **Verification Update**: PR reviews must include a `full-suite-audit` check if DTOs are modified.
---
### ID: TD-CRIT-FLOAT-SETTLE
### Title: Float-to-Int Migration Bridge
- **Symptom**: Core financial engines still pass `float` dollars instead of `int` pennies at several integration points.
- **Risk**: Cumulative rounding errors in long-running simulations (10,000+ ticks).
- **Solution**: Execute the global migration script to convert all `float` currency fields to `int` pennies.
- **Status**: Registered. Basis point depreciation (1/10000) implemented as a precursor.

---
### ID: TD-TEST-SSOT-SYNC
### Title: SSoT Balance Mismatch in Test Suite
- **Symptom**: `test_fiscal_integrity.py` (and potentially others) fails despite logic being correct, because assertions use `Agent.assets` (float/legacy) instead of `SettlementSystem.get_balance()` (int/SSoT).
- **Risk**: Masking of regression bugs. The transition to "Dual-Write Elimination" in `FinanceSystem` makes agent-level property updates unreliable.
- **Solution**: 
    1. Refactor `test_fiscal_integrity.py:L82` to use `settlement_system.get_balance(gov.id)`.
    2. Audit the entire integration test suite for similar stale assertions.
- **Status**: **Resolved** (Refactored `test_settlement_system.py`, `test_tax_incidence.py`, `verify_inheritance.py`, `verify_integrity_v2.py`, etc.).

---
### Architectural Note: CES Lite (Component-based Engine & Shell)
- **Achievement**: Successfully dismantled `Firm` into `IFinancialComponent` and `IInventoryComponent`.
- **Impact**: Solves **TD-124** (Firm God Class). All future agent expansions MUST follow the CES Lite pattern.
