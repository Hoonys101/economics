# Technical Debt Ledger (기술부채 관리대장)

> **Architectural Classification Update**: This ledger is organized by architectural domain to align with the system's core design principles (`ARCH_*.md`). Resolved debts are purged after each sprint.

## 🏛️ 1. AGENTS & POPULATIONS (`ARCH_AGENTS.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-006 | 2026-01-12 | Deterministic Class Caste (`core_agents.py`) | Agency 상실 및 Class 고착화 강제 | **DEFERRED** |
| TD-162 | 2026-01-30 | Bloated God Class: Household | Maintenance/Testing Overhead | **RESOLVED** |
| TD-169 | 2026-01-31 | Bloat Risk: `phases.py`, `government.py` | Emerging Maintenance Debt | **READY** |

## 🏭 2. FIRMS & CORPORATE

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-005 | 2026-01-12 | Hardcoded Halo Effect in `firms.py` | Marginal Product of Labor 이론 위배 | **DEFERRED** |
| TD-073 | 2026-01-20 | Firm Component State Ownership | Architectural purity | **DEFERRED** |
| TD-142 | 2026-01-29 | God File: `corporate_manager.py` | 629+ LOC complexity | **READY** |

## 🧠 3. DECISION & AI ENGINE (`ARCH_AI_ENGINE.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-141 | 2026-01-29 | God File: `ai_driven_household_engine.py` | 636+ LOC complexity | **READY** |

## 💹 4. MARKETS & ECONOMICS

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-007 | 2026-01-12 | Industrial Revolution Stress Test Config | 비현실적 경제 상태 (무한 수요) | **PENDING** |
| TDL-028 | 2026-01-29 | Inconsistent Order Object Structure | High Cognitive Load / Runtime Errors | **RESOLVED** |

## 💸 5. SYSTEMS & TRANSACTIONS (`ARCH_TRANSACTIONS.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-160 | 2026-01-30 | Transaction-Tax Atomicity Failure | Policy Revenue Leak | **RESOLVED** |
| TD-171 | 2026-01-31 | Liquidation Dust Leak (Household) | Escheatment missing, assets vanish | **RESOLVED** |
| TD-175 | 2026-01-31 | Manual Escrow Rollback Logic | Complex/Untested failure path (needs Saga) | **RESOLVED** |
| TD-176 | 2026-01-31 | Tight Coupling: TxManager & Govt | High Architectural dependency | **RESOLVED** |
| TD-177 | 2026-01-31 | HousingSystem Bypassing Markets | Economic purity violation | **RESOLVED** |


## 📦 6. DATA & DTO CONTRACTS

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-151 | 2026-01-29 | Partial DTO Adoption in Engine | Inconsistent Internal/External API | **READY** |
| TD-166 | 2026-01-31 | Configuration Duality (Engine vs Agent) | Configuration Fragmentation | **SPECCED** |
| TD-168 | 2026-01-31 | `make_decision` Abstraction Leak | Raw Agent objects in method signature | **READY** |

## 🧱 7. INFRASTRUCTURE & TESTING

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-122 | 2026-01-26 | Test Directory Organization | Maintenance overhead | **DEFERRED** |
| TD-140 | 2026-01-29 | God File: `db/repository.py` | 745+ LOC complexity | **RESOLVED** |

## 📜 8. OPERATIONS & DOCUMENTATION

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-150 | 2026-01-29 | Ledger Management Process | Loss of context | **ACTIVE** |

---

## ⚪ ABORTED / DEPRECATED (연구 중단)

| ID | Date | Description | Reason for Abort | Impact |
|---|---|---|---|---|
| TD-105 | 2026-01-23 | DLL Loading Failure (C++ Agent) | System environment constraints | Abandoned C++ |
| TD-135-v1 | 2026-01-28 | Operation Abstraction Wall (Initial) | Failed due to 'Mock-Magic' leaks | Architectural Bloat |
