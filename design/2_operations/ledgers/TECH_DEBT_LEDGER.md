# Technical Debt Ledger (기술부채 관리대장)

> **Architectural Classification Update**: This ledger is organized by architectural domain to align with the system's core design principles (`ARCH_*.md`). Resolved debts are purged after each sprint.

## 🏛️ 1. AGENTS & POPULATIONS (`ARCH_AGENTS.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-006 | 2026-01-12 | Deterministic Class Caste (`core_agents.py`) | Agency 상실 및 Class 고착화 강제 | **DEFERRED** |
| TD-162 | 2026-01-30 | Bloated God Class: Household | Maintenance/Testing Overhead | **ACTIVE** |
| TD-159 | 2026-01-30 | Legacy Inheritance Redundancy | Potential Double-Counting/Leak | **ACTIVE** |

## 🏭 2. FIRMS & CORPORATE

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-005 | 2026-01-12 | Hardcoded Halo Effect in `firms.py` | Marginal Product of Labor 이론 위배 | **DEFERRED** |
| TD-073 | 2026-01-20 | Firm Component State Ownership | Architectural purity | **DEFERRED** |
| TD-142 | 2026-01-29 | God File: `corporate_manager.py` | 629+ LOC complexity | **ACTIVE** |

## 🧠 3. DECISION & AI ENGINE (`ARCH_AI_ENGINE.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-141 | 2026-01-29 | God File: `ai_driven_household_engine.py` | 636+ LOC complexity | **ACTIVE** |

## 💹 4. MARKETS & ECONOMICS

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-007 | 2026-01-12 | Industrial Revolution Stress Test Config | 비현실적 경제 상태 (무한 수요) | **PENDING** |
| TDL-028 | 2026-01-29 | Inconsistent Order Object Structure | High Cognitive Load / Runtime Errors | **ACTIVE** |
| TD-157 | 2026-01-30 | Price-Consumption Deadlock | Economic Collapse (Static Price) | **IN_PROGRESS** |
| TD-164 | 2026-01-30 | Missing Fractional Reserve (WO-024) | Economic Stagnation / Liquidity Bottleneck | **CRITICAL** |

## 💸 5. SYSTEMS & TRANSACTIONS (`ARCH_TRANSACTIONS.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-160 | 2026-01-30 | Transaction-Tax Atomicity Failure | Policy Revenue Leak | **ACTIVE** |

## 📦 6. DATA & DTO CONTRACTS

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-118 | 2026-01-29 | DTO Contract Mismatch (inventory) | Runtime Errors / Confusion | **ACTIVE** |
| TD-151 | 2026-01-29 | Partial DTO Adoption in Engine | Inconsistent Internal/External API | **ACTIVE** |

## 🧱 7. INFRASTRUCTURE & TESTING

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-163 | 2026-01-30 | Test Suite Degradation (85+ Failures) | Zero Regression Guard | **CRITICAL** |
| TD-122 | 2026-01-26 | Test Directory Organization | Maintenance overhead | **DEFERRED** |
| TD-140 | 2026-01-29 | God File: `db/repository.py` | 745+ LOC complexity | **ACTIVE** |

## 📜 8. OPERATIONS & DOCUMENTATION

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-150 | 2026-01-29 | Ledger Management Process | Loss of context | **ACTIVE** |
| TD-143 | 2026-01-29 | Hardcoded Placeholders (WO-XXX) | Documentation Debt | **ACTIVE** |

---

## ⚪ ABORTED / DEPRECATED (연구 중단)

| ID | Date | Description | Reason for Abort | Impact |
|---|---|---|---|---|
| TD-105 | 2026-01-23 | DLL Loading Failure (C++ Agent) | System environment constraints | Abandoned C++ |
| TD-135-v1 | 2026-01-28 | Operation Abstraction Wall (Initial) | Failed due to 'Mock-Magic' leaks | Architectural Bloat |
