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
| **TD-SYS-ACCOUNTING-GAP** | Systems | `accounting.py` misses tracking buyer expenses. | **Medium**: Accuracy. | Open |
| **TD-ECON-M2-INV-BUG** | Economic | **M2 Audit Logic**: `audit_total_m2` naively sums negative balances. | **CRITICAL**: Integrity. | **RESOLVED** |
| **TD-SYS-BATCH-RACE** | Finance | **Atomic Batch Race**: Multiple withdrawals in a batch bypass balance checks. | **High**: Soundness. | **RESOLVED** |
| **TD-TEST-TX-MOCK-LAG** | Testing | **Transaction Test Lag**: `test_transaction_engine.py` mocks are out of sync. | **Low**: Flakiness. | Identified |
| **TD-TEST-TAX-DEPR** | Testing | **Deprecated Tax API in Tests**: `test_transaction_handlers.py` still uses `collect_tax`. | **Medium**: Tech Debt. | **IDENTIFIED (WV6)** |
| **TD-ECON-INSTABILITY-V2** | Economic | **Rapid Collapse**: Sudden Zombie/Fire Sale clusters despite high initial assets. | **High**: Logic Drift. | **IDENTIFIED** |
| **TD-ARCH-ORCH-HARD** | Architecture | **Orchestrator Fragility**: `TickOrchestrator` lacks hardening against missing DTO attributes in mocks. | **Medium**: Resilience. | **NEW (PH21)** |
| **TD-ARCH-SETTLEMENT-BLOAT** | Architecture | **Settlement Overload**: `SettlementSystem` handles orchestration, ledgers, metrics, and indices. | **High**: Maintainability. | **RESOLVED (PH4.1)** |
| **TD-CONFIG-HARDCODED-MAJORS** | Configuration | **Hardcoded Majors**: `MAJORS` list hardcoded in `labor/constants.py` instead of yaml. | **Low**: Flexibility. | **RESOLVED (PH4.1)** |
| **TD-ECON-M2-REGRESSION** | Economic | **M2 Negative Inversion**: `calculate_total_money()` sums negative balances. | **CRITICAL**: Integrity. | **RESOLVED (PH23)** |
| **TD-FIN-SAGA-REGRESSION** | Finance | **Saga Drift**: Sagas skipped due to missing/dead participant IDs. | **High**: Protocol. | **RESOLVED (PH23)** |
| **TD-LIFECYCLE-GHOST-FIRM** | Lifecycle | **Ghost Firm Bug**: Transactions precede registration during startup. | **CRITICAL**: Integrity. | **RESOLVED (PH23)** |
| **TD-BANK-RESERVE-CRUNCH** | Finance | **Reserve Constraint**: Bank 2 lacks reserves (1M) to fund infrastructure bonds (8M+). | **Medium**: Logic. | **NEW** |
| **TD-ECON-ZOMBIE-FIRM** | Economic | **Firm Extinction**: Rapid collapse of basic_food firms causing FIRE_SALE spam. | **High**: Balance. | **NEW** |
| **TD-ARCH-SEO-LEGACY** | Firm | **Legacy SEO Gap**: `brain_scan` skips legacy decision logic unless mocked. | **Medium**: AI Integrity. | **NEW (PH4.1)** |
| **TD-TEST-DTO-MOCK** | Testing | **DTO Hygiene**: `tests/test_firm_brain_scan.py` uses permissive `MagicMock` for DTOs. | **Low**: Stability. | **RESOLVED (PH4.1)** |
| **TD-LIFECYCLE-NAMING** | Lifecycle | **Variable Naming**: `capital_stock_pennies` multiplied by 100, implies units. | **Medium**: Inflation. | **NEW (PH4.1)** |
| **TD-LABOR-METADATA** | Market | LaborMarket uses `Order.metadata` for Major matching instead of DTO. | **Low**: Typing. | **NEW (PH4.1)** |
| **TD-FIN-MAGIC-BASE-RATE** | Finance | `FinanceSystem.issue_treasury_bonds` uses hardcoded `0.03`. | **Low**: Config. | Identified |
| **TD-WAVE3-DTO-SWAP** | DTO | **IndustryDomain Shift**: Replace `major` with `IndustryDomain` enum. | **Medium**: Structure. | **SPECCED** |
| **TD-WAVE3-TALENT-VEIL** | Agent | **Hidden Talent**: `EconStateDTO` missing `hidden_talent`. | **High**: Intent. | **SPECCED** |
| **TD-WAVE3-MATCH-REWRITE** | Market | **Bargaining vs OrderBook**: Existing LaborMarket assumes sorting. | **High**: Economy. | **SPECCED** |
| **TD-FIN-INVISIBLE-HAND** | Finance | **Initialization Order**: CB/PublicManager registered after AgentRegistry snapshot. | **CRITICAL**: Runtime failure. | **RESOLVED (PH23)** |
| **TD-MARKET-FLOAT-TRUNC** | Market | **Wealth Destruction**: `MatchingEngine` truncates fractional pennies via `int()`. | **High**: Deflationary bias. | **RESOLVED (PH23)** |
| **TD-SYS-ANALYTICS-DIRECT** | Systems | **Stateless Bypass**: `AnalyticsSystem` calls agent methods instead of using DTO snapshots. | **Medium**: Pattern violation. | Open |
| **TD-TEST-MOCK-REGRESSION** | Testing | **Cockpit Stale Attr**: `system_command_queue` used in mocks instead of `system_commands`. | **High**: Testing Gap. | **NEW (AUDIT)** |
| **TD-ARCH-ESTATE-REGISTRY** | Lifecycle | **Post-Mortem Integrity**: Missing graveyard registry for dead agents' transactions. | **High**: Financial soundness. | **SPECCED (PH33)** |
| **TD-SPEC-DTO-INT-MIGRATION** | DTO | **Telemetry Precision**: `SettlementResultDTO` still uses floats for reporting. | **Medium**: Consistency. | **SPECCED (PH33)** |
| **TD-FIN-LIQUIDATION-DUST** | Finance | **Wealth Orphanage**: Pro-rata liquidation truncates dust pennies. | **Low**: Accuracy. | **SPECCED (PH33)** |
| **TD-REBIRTH-BUFFER-LOSS** | Architecture | **Buffer Flush Risk**: Crash during simulation results in loss of up to N ticks of data. | **Medium**: Data Loss. | **NEW (PH34)** |
| **TD-REBIRTH-TIMELINE-OPS** | Configuration | **Dynamic Shift Handling**: Config DTOs are immutable; re-generation needed during events. | **High**: Logic Complexity. | **NEW (PH34)** |
| **TD-TEST-LIFECYCLE-STALE-MOCK** | Testing | **Stale Method Access**: `test_engine.py` calls deprecated `_handle_agent_liquidation`. | **Medium**: Failure. | **NEW (AUDIT)** |
| **TD-ARCH-GOD-CMD-DIVERGENCE** | Architecture | **Naming Drift**: `god_command_queue` (deque) vs `god_commands` (list). | **Low**: Confusion. | **NEW (AUDIT)** |
| **TD-ARCH-GOV-DYNAMIC** | Architecture | **Fragile Injection**: `state.government` rely on dynamic `__setattr__` in initializer. | **Medium**: Flakiness. | **NEW (AUDIT)** |
| **TD-LIFECYCLE-CONFIG-PARITY** | Lifecycle | **Config Parity**: Birth/Death systems still use raw config vs DTO. | **Medium**: Inconsistency. | **NEW (PH34)** |

---

## Architecture & Infrastructure
---
### ID: TD-ARCH-SETTLEMENT-BLOAT
- **Title**: SettlementSystem Responsibility Overload
- **Symptom**: `SettlementSystem` handles transaction orchestration, ledger delegation, internal bank indexing (`_bank_depositors`), and metrics.
- **Risk**: High coupling makes future FX/Market expansions (multi-hop swaps) difficult to test and maintain.
- **Solution**: Extract `BankRegistry` and `MetricsRecording` into dedicated services. Keep `SettlementSystem` purely for orchestration.
- **Status**: RESOLVED (Phase 4.1)

### ID: TD-ARCH-GOV-MISMATCH / TD-ARCH-GOV-DYNAMIC
- **Title**: Singleton vs List & Fragile Injection
- **Symptom**: `WorldState` has `governments` (List) but `TickOrchestrator` uses `state.government`. Relies on dynamic `setattr` in initializer.
- **Risk**: Test fragility; `AttributeError` in unit tests where initializer is bypassed.
- **Solution**: Implement a `@property` or explicit facade in `WorldState` to provide a singular `government` reference.

### ID: TD-ARCH-GOD-CMD-DIVERGENCE
- **Title**: God Command Naming Divergence
- **Symptom**: `WorldState` uses `god_command_queue` (deque) while `SimulationState` DTO uses `god_commands` (list).
- **Risk**: Confusion during DTO construction and inconsistency across the command pipeline.
- **Solution**: Synchronize naming to `god_commands` across both classes and use `deque` only internally if needed for performance.

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
- **Symptom**: Massive spam of `SAGA_SKIP` logs with missing participant IDs. Sagas persist references to dead/failed agents.
- **Risk**: Transactions fail to complete; orphaned processes consume compute cycles.
- **Solution**: Re-verify ID propagation in `TickOrchestrator`. Implement saga cleanup for dead participants.
- **Status**: RESOLVED (Phase 23)

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

### ID: TD-FIN-MAGIC-BASE-RATE
- **Title**: Magic Number for Base Interest Rate
- **Symptom**: `FinanceSystem.issue_treasury_bonds` uses a hardcoded `0.03` fallback when no banks are available.
- **Risk**: Lack of configurability and transparency.
- **Solution**: Define a named constant in `modules.finance.constants`.
- **Status**: Identified (Follow-up from BankRegistry Extraction)


## AI & Economic Simulation
---
### ID: TD-ECON-M2-REGRESSION
- **Title**: M2 Negative Inversion (Regression)
- **Symptom**: Aggregate money supply goes negative (`Current: -153521427.00`).
- **Risk**: Deflationary spiral, math errors in interest calculation.
- **Solution**: Update `calculate_total_money()` to `Sum(max(0, balance_i))`. Track negative balances as `SystemDebt`, not M2 deduction.
- **Status**: RESOLVED (Phase 23)

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
### ID: TD-ARCH-ESTATE-REGISTRY
- **Title**: Estate/Graveyard Registry for Dead Agents
- **Symptom**: SettlementSystem currently uses a "Resurrection Hack" to handle post-mortem transactions.
- **Risk**: Data corruption and lifecycle violations if dead agents are partially re-injected.
- **Solution**: Implement a formal `EstateRegistry` to manage financial finalization for liquidated agents without re-registration.
- **Status**: SPECCED (Phase 33)

### ID: TD-LIFECYCLE-GHOST-FIRM
- **Title**: Atomic Startup Failure (Ghost Firm Bug)
- **Symptom**: `SETTLEMENT_FAIL | Engine Error: Destination account does not exist: [IDs]`.
- **Risk**: Capital injections fail silently, leaving firms in "Zombie" states. Investor funds may be debited without corresponding credit.
- **Solution**: Implement `FirmFactory` to ensure Registration -> Bank Account Opening -> Injection sequence is atomic and blocking.
- **Status**: RESOLVED (Phase 23)

### ID: TD-CONFIG-HARDCODED-MAJORS
- **Title**: Hardcoded Labor Majors
- **Symptom**: `MAJORS` list is currently hardcoded in `modules/labor/constants.py`.
- **Risk**: Adding new sectors requires code changes rather than just adjusting `economy_params.yaml`.
- **Solution**: Move `MAJORS` definitions to `economy_params.yaml` or a dedicated sector config file.
- **Status**: RESOLVED (Phase 4.1)

---

## DX & Cockpit Operations
---
- **Status**: RESOLVED (Wave 6) - Restored lazy imports and optimized dispatcher context.

### ID: TD-SYS-TRANSFER-HANDLER-GAP
- **Title**: Generic Transfer Handler Omission
- **Symptom**: `SettlementSystem._create_transaction_record` hardcodes `transaction_type="transfer"`. The `TransactionProcessor` lacks a handler for this type, causing P2P transfers to be silently skipped during ledger processing.
- **Risk**: Absolute accounting failure for non-market transfers. The `MonetaryLedger` only sees transactions with specialized handlers (LLR, Tax, Goods), creating a massive "dark pool" of money movement.
- **Solution**: Register a `DefaultTransferHandler` in `initializer.py` or update `SettlementSystem` to use specific types for all operations.
- **Status**: RESOLVED (Wave 6) - `DefaultTransferHandler` implemented and registered.

---

## Testing & Quality Assurance
---
### ID: TD-TEST-MOCK-REGRESSION
- **Title**: Cockpit Mock Attribute Regressions
- **Symptom**: Tests (e.g. `test_state_synchronization.py`) use deprecated `system_command_queue` on `WorldState` mocks.
- **Risk**: Silent coverage loss; Cockpit commands are ignored in tests but tests pass.
- **Solution**: Update mocks to use `system_commands` (list).

### ID: TD-TEST-LIFECYCLE-STALE-MOCK
- **Title**: Stale Lifecycle Method Access
- **Symptom**: `tests/system/test_engine.py` attempts to call `_handle_agent_liquidation` which was refactored into `DeathSystem`.
- **Risk**: Test failures in the system engine suite.
- **Solution**: Realign test logic to use `DeathSystem` or mock the new lifecycle components accurately.

---

## Lifecycle & Configuration
---
### ID: TD-LIFECYCLE-CONFIG-PARITY
- **Title**: Lifecycle Subsystem Config Parity
- **Symptom**: `AgingSystem` uses a strictly typed `LifecycleConfigDTO`, while `BirthSystem` and `DeathSystem` in `AgentLifecycleManager` still depend on the raw `config_module` object.
- **Risk**: Inconsistent configuration access patterns across lifecycle subsystems, leading to mixed float/penny math boundaries and potential runtime type errors in death/birth execution paths.
- **Solution**: Implement `BirthConfigDTO` and `DeathConfigDTO` to fully decouple all lifecycle systems from the global config module, completing the dependency injection refactoring.
- **Status**: NEW (Phase 34)

---
> [!NOTE]
> ✅ **Resolved Debt History**: For clarity, all resolved technical debt items and historical lessons have been moved to [TECH_DEBT_HISTORY.md](./TECH_DEBT_HISTORY.md).
