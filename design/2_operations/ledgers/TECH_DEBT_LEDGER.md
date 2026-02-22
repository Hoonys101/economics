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
| **TD-ARCH-GOV-MISMATCH** | Architecture | **Singleton vs List**: `WorldState` has `governments` (List) vs Singleton `government`. | **Medium**: Logic Drift. | Open |
| **TD-INT-BANK-ROLLBACK** | Finance | **Rollback Coupling**: Bank rollback logic dependent on `hasattr` implementation. | **Low**: Leak. | Open |
| **TD-SYS-ACCOUNTING-GAP** | Systems | **Accounting Accuracy**: `accounting.py` misses tracking buyer expenses. | **Medium**: Accuracy. | Open |
| **TD-TEST-TX-MOCK-LAG** | Testing | **Transaction Test Lag**: `test_transaction_engine.py` mocks are out of sync. | **Low**: Flakiness. | Identified |
| **TD-TEST-TAX-DEPR** | Testing | **Deprecated Tax API in Tests**: `test_transaction_handlers.py` still uses `collect_tax`. | **Medium**: Tech Debt. | Identified |
| **TD-ECON-INSTABILITY-V2** | Economic | **Rapid Collapse**: Sudden Zombie/Fire Sale clusters despite high initial assets. | **High**: Logic Drift. | **IDENTIFIED** |
| **TD-ARCH-ORCH-HARD** | Architecture | **Orchestrator Fragility**: `TickOrchestrator` lacks hardening against missing DTO attributes in mocks. | **Medium**: Resilience. | **NEW (PH21)** |
| **TD-ARCH-SETTLEMENT-BLOAT** | Architecture | **Settlement Overload**: `SettlementSystem` handles orchestration, ledgers, metrics, and indices. | **High**: Maintainability. | **NEW (PH4.1)** |
| **TD-CONFIG-HARDCODED-MAJORS** | Configuration | **Hardcoded Majors**: `MAJORS` list hardcoded in `labor/constants.py` instead of yaml. | **Low**: Flexibility. | **NEW (PH4.1)** |
| **TD-ECON-M2-REGRESSION** | Economic | **M2 Inversion Regression**: Money supply drops negative (e.g., -153M). | **CRITICAL**: Integrity. | **REGRESSION** |
| **TD-FIN-SAGA-REGRESSION** | Finance | **Saga Drift Regression**: Sagas skipped due to missing participant IDs. | **High**: Protocol. | **REGRESSION** |
| **TD-BANK-RESERVE-CRUNCH** | Finance | **Reserve Constraint**: Bank 2 lacks reserves (1M) to fund infrastructure bonds (8M+). | **Medium**: Logic. | **NEW** |
| **TD-ECON-ZOMBIE-FIRM** | Economic | **Firm Extinction**: Rapid collapse of basic_food firms causing FIRE_SALE spam. | **High**: Balance. | **NEW** |
| **TD-ARCH-SEO-LEGACY** | Firm | **Legacy SEO Gap**: `brain_scan` skips legacy decision logic unless mocked. | **Medium**: AI Integrity. | **NEW (PH4.1)** |
| **TD-TEST-DTO-MOCK** | Testing | **DTO Hygiene**: `tests/test_firm_brain_scan.py` uses permissive `MagicMock` for DTOs. | **Low**: Stability. | **NEW (PH4.1)** |
| **TD-LIFECYCLE-NAMING** | Lifecycle | **Variable Naming**: `capital_stock_pennies` multiplied by 100, implies units. | **Medium**: Inflation. | **NEW (PH4.1)** |
| **TD-LABOR-METADATA** | Market | **Order Payload**: LaborMarket uses `Order.metadata` for Major matching instead of DTO. | **Low**: Typing. | **NEW (PH4.1)** |

---

## Architecture & Infrastructure
---
### ID: TD-ARCH-SETTLEMENT-BLOAT
- **Title**: SettlementSystem Responsibility Overload
- **Symptom**: `SettlementSystem` handles transaction orchestration, ledger delegation, internal bank indexing (`_bank_depositors`), and metrics.
- **Risk**: High coupling makes future FX/Market expansions (multi-hop swaps) difficult to test and maintain.
- **Solution**: Extract `BankRegistry` and `MetricsRecording` into dedicated services. Keep `SettlementSystem` purely for orchestration.
- **Status**: Identified (Phase 4.1)

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

### ID: TD-FIN-SAGA-REGRESSION
- **Title**: Saga Participant Drift (Regression)
- **Symptom**: Massive spam of `SAGA_SKIP` logs with missing participant IDs.
- **Risk**: Transactions, specially complex workflows, fail to complete, destroying protocol execution rates.
- **Solution**: Revisit Saga definitions or the state injection in `TickOrchestrator` to ensure IDs are propagated correctly.
- **Status**: REGRESSION (Phase 4.1 Diagnostics)

### ID: TD-BANK-RESERVE-CRUNCH
- **Title**: Bank Reserve Structural Constraint
- **Symptom**: `BOND_ISSUANCE_FAILED` because Bank 2 only has 1,000,000 pennies in reserves but tries to issue bonds for 8M - 40M.
- **Risk**: Macroeconomic scale of the government is completely stunted because central/commercial banks lack fractional elasticity.
- **Solution**: Implement proper fractional reserve system or inject more liquidity early on.
- **Status**: NEW

### ID: TD-INT-BANK-ROLLBACK
- **Title**: Rollback Coupling
- **Symptom**: Bank rollback logic dependent on `hasattr` implementation details.
- **Risk**: Abstraction Leak.
- **Solution**: Move rollback logic to `TransactionProcessor` and use strict protocols.


## AI & Economic Simulation
---
### ID: TD-ECON-M2-REGRESSION
- **Title**: M2 Negative Inversion (Regression)
- **Symptom**: Aggregate money supply goes negative (`Current: -153521427.00`).
- **Risk**: Deflationary spiral, math errors in interest calculation.
- **Solution**: The distinction between liquidity and liability added earlier was either reverted or bypassing standard accounting loops. Needs investigation.
- **Status**: REGRESSION (Phase 4.1 Diagnostics)

### ID: TD-ECON-ZOMBIE-FIRM
- **Title**: Rapid Extinction of basic_food Firms
- **Symptom**: Firms (e.g., Firm 121, 122) trigger `FIRE_SALE` continually, go `ZOMBIE` (cannot afford wage), and then `FIRM_INACTIVE` within the first 30 ticks.
- **Risk**: Destruction of the simulation economy early in the run.
- **Solution**: Re-tune pricing constraints, initial reserves, or labor cost expectations specifically for essential goods.
- **Status**: NEW

### ID: TD-LABOR-METADATA
- **Title**: Order Metadata Refactor for Labor Matches
- **Symptom**: The `LaborMarket` currently uses `Order.metadata` to pass major information rather than strongly typed logic.
- **Risk**: Abstraction leak in the order pipeline. 
- **Solution**: Refactor to pass Major information through native DTOs.
- **Status**: NEW

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


## Lifecycle & Configuration
---
### ID: TD-CONFIG-HARDCODED-MAJORS
- **Title**: Hardcoded Labor Majors
- **Symptom**: `MAJORS` list is currently hardcoded in `modules/labor/constants.py`.
- **Risk**: Adding new sectors requires code changes rather than just adjusting `economy_params.yaml`.
- **Solution**: Move `MAJORS` definitions to `economy_params.yaml` or a dedicated sector config file.
- **Status**: Identified (Phase 4.1)

---
> [!NOTE]
> ✅ **Resolved Debt History**: For clarity, all resolved technical debt items and historical lessons have been moved to [TECH_DEBT_HISTORY.md](./TECH_DEBT_HISTORY.md).
