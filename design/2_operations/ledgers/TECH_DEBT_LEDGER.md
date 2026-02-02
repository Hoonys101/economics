# Technical Debt Ledger (기술부채 관리대장)

> **Architectural Classification Update**: This ledger is organized by architectural domain to align with the system's core design principles (`ARCH_*.md`). Resolved debts are purged after each sprint.

## 🏛️ 1. AGENTS & POPULATIONS (`ARCH_AGENTS.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-006 | 2026-01-12 | Deterministic Class Caste (`core_agents.py`) | Agency 상실 및 Class 고착화 강제 | **DEFERRED** |
| TD-162 | 2026-01-30 | Bloated God Class: Household (977 lines) | SRP violation; property delegation bloat | **ACTIVE** |
| TD-180 | 2026-02-01 | TestFile Bloat: `test_firm_decision_engine_new.py` | 828 lines; indicator of complex engine surface | **WARNING** |

## 🏭 2. FIRMS & CORPORATE

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-005 | 2026-01-12 | Hardcoded Halo Effect in `firms.py` | Marginal Product of Labor 이론 위배 | **DEFERRED** |
| TD-073 | 2026-01-20 | Firm Component State Ownership | Architectural purity | **DEFERRED** |
| TD-190 | 2026-02-01 | Complex `if/elif` chain in `_execute_internal_order` | `firms.py` implementation complexity | **ACTIVE** |

## 🧠 3. DECISION & AI ENGINE (`ARCH_AI_ENGINE.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-181 | 2026-02-01 | Abstraction Leak: `DecisionUnit` Direct Market Access | Tight coupling; bypasses MarketSnapshotDTO | **RESOLVED** |
| TD-182 | 2026-02-01 | Abstraction Leak: `make_decision` signature | Passing raw market objects allows mutation risk | **RESOLVED** |
| TD-189 | 2026-02-01 | God Method: `Phase1_Decision.execute` | Excessive orchestration complexity in `phases.py` | **RESOLVED** |

## 💹 4. MARKETS & ECONOMICS

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| (Empty) | | | | |

## 💸 5. SYSTEMS & TRANSACTIONS (`ARCH_TRANSACTIONS.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-191 | 2026-02-01 | God Method/Class: `TransactionProcessor.execute` | Violates SRP; excessive branching logic | **RESOLVED** |
| TD-191-B | 2026-02-01 | Public Manager Integration Gaps | PublicManager lacks full IFinancialEntity compliance; ID type mismatch (String vs Int) | **RESOLVED** |

## 📦 6. DATA & DTO CONTRACTS

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| **HousingRefactor** | 2026-01-31 | Orphaned Housing Logic (Mortgage Bypass) | **CRITICAL** | **ACTIVE** | Housing market functional failure. |
| TD-065 | 2026-01-31 | Duplicated Housing Decision Logic | Maintenance Risk | **ACTIVE** | Consolidated housing logic pending. |
| TD-193 | 2026-02-02 | Mutable StockOrders in Market | Immutability Violation | **RESOLVED** |
| TD-194 | 2026-02-02 | Abstraction Leak: `DecisionInputDTO` | Raw market access in DTO | **RESOLVED** |
| WO-142 | 2026-02-02 | Floating Point Precision Leak | Zero-Sum Violation | **RESOLVED** |

## 🧱 7. INFRASTRUCTURE & TESTING

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-122 | 2026-01-26 | Test Directory Organization | Maintenance overhead | **DEFERRED** |
| TDL-029 | 2026-01-31 | ViewModel DI Violation (Repository) | Tight Coupling | **RESOLVED** | ViewModels correctly receive SimulationRepository via DI. |
| TD-192 | 2026-02-01 | ActionProcessor Transient State Synchronization Risk | Regression risk | **ACTIVE** | Manual sync of `SimulationState` needed. |

## 📜 8. OPERATIONS & DOCUMENTATION

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-150 | 2026-01-29 | Ledger Management Process | Loss of context | **ACTIVE** |
| TD-183 | 2026-02-01 | Sequence Deviation Documentation | Fast-Fail Liquidation needs ARCH entry | **ACTIVE** |
| TD-188 | 2026-02-01 | Inconsistent Config Path Doc | `PROJECT_STATUS.md` path mismatch | **ACTIVE** |

---

## ⚪ ABORTED / DEPRECATED (연구 중단)

| ID | Date | Description | Reason for Abort | Impact |
|---|---|---|---|---|
| TD-105 | 2026-01-23 | DLL Loading Failure (C++ Agent) | System environment constraints | Abandoned C++ |
| TD-135-v1 | 2026-01-28 | Operation Abstraction Wall (Initial) | Failed due to 'Mock-Magic' leaks | Architectural Bloat |
