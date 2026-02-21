# Technical Debt Ledger (TECH_DEBT_LEDGER.md)

## 📑 Table of Contents
1. [Core Summary Table](#-core-summary-table)
2. [Architecture & Infrastructure](#architecture--infrastructure)
3. [Financial Systems (Finance & Transactions)](#financial-systems-finance--transactions)
4. [AI & Economic Simulation](#ai--economic-simulation)
5. [Market & Systems](#market--systems)
6. [Lifecycle & Configuration](#lifecycle--configuration)
7. [Testing & Quality Assurance](#testing--quality-assurance)
8. [DX & Cockpit Operations](#dx--cockpit-operations)

---

## 📊 Core Summary Table

| ID | Module / Component | Description | Priority / Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TD-ARCH-FIRM-COUP** | Architecture | **Parent Pointer Pollution**: `Firm` departments use `self.parent`, bypassing Orchestrator. | **High**: Structural Integrity. | Open |
| **TD-ARCH-GOV-MISMATCH** | Architecture | **Singleton vs List**: `WorldState` has `governments` (List) vs Singleton `government`. | **Medium**: Logic Drift. | Open |
| **TD-CRIT-FLOAT-CORE** | Finance | **Float Core**: `SettlementSystem` and `MatchingEngine` use `float` instead of `int`. | **Critical**: Determinism. | **PARTIAL** |
| **TD-INT-BANK-ROLLBACK** | Finance | **Rollback Coupling**: Bank rollback logic dependent on `hasattr` implementation. | **Low**: Leak. | Open |
| **TD-RUNTIME-TX-HANDLER** | Transaction | **Missing Handler**: `bailout`, `bond_issuance` tx types not registered. | **High**: Failure. | Open |
| **TD-SYS-ACCOUNTING-GAP** | Systems | **Accounting Accuracy**: `accounting.py` misses tracking buyer expenses. | **Medium**: Accuracy. | Open |
| **TD-TEST-TX-MOCK-LAG** | Testing | **Transaction Test Lag**: `test_transaction_engine.py` mocks are out of sync. | **Low**: Flakiness. | Identified |
| **TD-TEST-COCKPIT-MOCK** | Testing | **Cockpit 2.0 Mock Regressions**: Tests use deprecated `system_command_queue`. | **High**: Silent Failure. | Identified |
| **TD-TEST-LIFE-STALE** | Testing | **Stale Lifecycle Logic**: `test_engine.py` calls refactored liquidation methods. | **High**: Breakdown. | Identified |
| **TD-TEST-TAX-DEPR** | Testing | **Deprecated Tax API in Tests**: `test_transaction_handlers.py` still uses `collect_tax`. | **Medium**: Tech Debt. | Identified |
| **TD-ECON-INSTABILITY-V2** | Economic | **Rapid Collapse**: Sudden Zombie/Fire Sale clusters despite high initial assets. | **High**: Logic Drift. | **IDENTIFIED** |
| **TD-ARCH-ORCH-HARD** | Architecture | **Orchestrator Fragility**: `TickOrchestrator` lacks hardening against missing DTO attributes in mocks. | **Medium**: Resilience. | **NEW (PH21)** |
| **TD-ECON-M2-INV** | Economic | **M2 Inversion**: Negative money supply due to overdrafts subtracted from aggregate cash. | **CRITICAL**: Integrity. | **NEW (PH21)** |
| **TD-ARCH-STARTUP-RACE** | Architecture | **Ghost Firm Registry**: Transactions attempted before agent/bank registration. | **High**: Failure. | **IDENTIFIED** |
| **TD-FIN-SAGA-ORPHAN** | Finance | **Saga Participant Drift**: Missing or stale participant IDs causing `SAGA_SKIP`. | **Medium**: Logic Gap. | **IDENTIFIED** |

---

## Architecture & Infrastructure
---
### ID: TD-ARCH-GOV-MISMATCH
- **Title**: Singleton vs List Mismatch
- **Symptom**: `WorldState` has `governments` (List) vs Singleton `government`.
- **Risk**: Logic Fragility.
- **Solution**: Standardize on a single representation for government access.

---

## Financial Systems (Finance & Transactions)
---
### ID: TD-CRIT-FLOAT-CORE (M&A Expansion)
- **Title**: M&A and Stock Market Float Violation
- **Symptom**: `MAManager` passes `float` offer prices to settlement, causing errors.
- **Risk**: Runtime crash during hostile takeovers or mergers.
- **Solution**: Quantize all valuations using `round_to_pennies()`.

### ID: TD-INT-BANK-ROLLBACK
- **Title**: Rollback Coupling
- **Symptom**: Bank rollback logic dependent on `hasattr` implementation details.
- **Risk**: Abstraction Leak.
- **Solution**: Move rollback logic to `TransactionProcessor` and use strict protocols.

### ID: TD-RUNTIME-TX-HANDLER
- **Title**: Missing Transaction Handlers
- **Symptom**: `bailout`, `bond_issuance` tx types not registered.
- **Risk**: Runtime Failure.
- **Solution**: Register all transaction types with the `TransactionEngine`.

---

## AI & Economic Simulation
---
### ID: TD-SYS-ACCOUNTING-GAP
- **Title**: Missing Buyer Expense Tracking
- **Symptom**: `accounting.py` fails to track expenses for raw materials on the buyer's side.
- **Risk**: Asymmetric financial logging that complicates GDP and profit analyses.
- **Solution**: Update Handler and `accounting.py` to ensure reciprocal debit/credit logging.

### ID: TD-ECON-M2-INV
- **Title**: M2 Negative Inversion
- **Symptom**: Aggregate money supply becomes negative when debt > cash.
- **Risk**: Simulation logic breaks (interest rates, policy) when "Money" is negative.
- **Solution**: Distinguish Liquidity from Liability in `calculate_total_money()`.

### ID: TD-ARCH-STARTUP-RACE
- **Title**: Firm Startup Race Condition
- **Symptom**: `SETTLEMENT_FAIL` during `spawn_firm` due to missing destination account.
- **Risk**: New firms start as zombies or fail to launch entirely.
- **Solution**: Implement blocking `open_account` before capital injection transaction.

---
> [!NOTE]
> ✅ **Resolved Debt History**: For clarity, all resolved technical debt items and historical lessons have been moved to [TECH_DEBT_HISTORY.md](./TECH_DEBT_HISTORY.md).
