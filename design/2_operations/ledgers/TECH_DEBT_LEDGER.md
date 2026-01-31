# Technical Debt Ledger (기술부채 관리대장)

> **Architectural Classification Update**: This ledger is organized by architectural domain to align with the system's core design principles (`ARCH_*.md`). Resolved debts are purged after each sprint.

## 🏛️ 1. AGENTS & POPULATIONS (`ARCH_AGENTS.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-006 | 2026-01-12 | Deterministic Class Caste (`core_agents.py`) | Agency 상실 및 Class 고착화 강제 | **DEFERRED** |
| TD-162 | 2026-01-30 | Bloated God Class: Household (977 lines) | SRP violation; property delegation bloat | **ACTIVE** |
| TD-169 | 2026-01-31 | Bloat Risk: `phases.py`, `government.py` | Emerging Maintenance Debt | **RESOLVED**|
| TD-180 | 2026-02-01 | TestFile Bloat: `test_firm_decision_engine_new.py` | 828 lines; indicator of complex engine surface | **WARNING** |

## 🏭 2. FIRMS & CORPORATE

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-005 | 2026-01-12 | Hardcoded Halo Effect in `firms.py` | Marginal Product of Labor 이론 위배 | **DEFERRED** |
| TD-073 | 2026-01-20 | Firm Component State Ownership | Architectural purity | **DEFERRED** |
| TD-142 | 2026-01-29 | God File: `corporate_manager.py` | 629+ LOC complexity | **RESOLVED** |

## 🧠 3. DECISION & AI ENGINE (`ARCH_AI_ENGINE.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-141 | 2026-01-29 | God File: `ai_driven_household_engine.py` | 636+ LOC complexity | **RESOLVED** |
| TD-181 | 2026-02-01 | Abstraction Leak: `DecisionUnit` Direct Market Access | Tight coupling; bypasses MarketSnapshotDTO | **ACTIVE** |
| TD-182 | 2026-02-01 | Abstraction Leak: `make_decision` signature | Passing raw market objects allows mutation risk | **ACTIVE** |

## 💹 4. MARKETS & ECONOMICS

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| **TD-007** | Malthusian Trap (Stagnation) | LOW | 2026-01-31 | **RESOLVED** | Long-term growth stagnation logic. |
| TDL-028 | 2026-01-29 | Inconsistent Order Object Structure | High Cognitive Load / Runtime Errors | **RESOLVED** |

## 💸 5. SYSTEMS & TRANSACTIONS (`ARCH_TRANSACTIONS.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-160 | 2026-01-30 | Transaction-Tax Atomicity (Inheritance) | Inheritance distribution is non-atomic loop | **ACTIVE** |
| TD-171 | 2026-01-31 | Liquidation Dust Leak (Escheatment) | Escheatment uses static vs dynamic assets | **ACTIVE** |
| TD-175 | 2026-01-31 | Manual Escrow Rollback Logic | Complex/Untested failure path (needs Saga) | **RESOLVED** |
| TD-176 | 2026-01-31 | Tight Coupling: TxManager & Govt | High Architectural dependency | **RESOLVED** |
| TD-177 | 2026-01-31 | HousingSystem Bypassing Markets | Economic purity violation | **RESOLVED** |
| **TD-178** | LoanMarket Phantom Liquidity Bug | HIGH | 2026-01-31 | **RESOLVED** | Double-counting in M2 due to redundant cash transfers. |
| **TD-179** | Ambiguous Asset Definition (Cash vs Deposit) | MED | 2026-01-31 | **RESOLVED** | Explicit accounting for M0/M1/M2 assets in DTOs. |
| TD-187 | 2026-02-01 | Direct Mutation Bypass (`pay_severance`) | Bypasses SettlementSystem ledger | **ACTIVE** |

## 📦 6. DATA & DTO CONTRACTS

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-151 | 2026-01-29 | Partial DTO Adoption in Engine | Inconsistent Internal/External API | **RESOLVED** |
| TD-166 | 2026-01-31 | Configuration Duality (Engine vs Agent) | Configuration Fragmentation | **RESOLVED** |
| TD-168 | 2026-01-31 | `make_decision` Abstraction Leak | Raw Agent objects in method signature | **RESOLVED** |
| **HousingRefactor** | 2026-01-31 | Orphaned Housing Logic (Mortgage Bypass) | **CRITICAL** | **ACTIVE** | Housing market functional failure. |
| TD-065 | 2026-01-31 | Duplicated Housing Decision Logic | Maintenance Risk | **ACTIVE** | Consolidated housing logic pending. |

## 🧱 7. INFRASTRUCTURE & TESTING

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-122 | 2026-01-26 | Test Directory Organization | Maintenance overhead | **DEFERRED** |
| TD-140 | 2026-01-29 | God File: `db/repository.py` | 745+ LOC complexity | **RESOLVED** |
| TDL-029 | 2026-01-31 | ViewModel DI Violation (Repository) | Tight Coupling | **ACTIVE** | ViewModels create own repository instances. |

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
