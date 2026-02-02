# Technical Debt Ledger (기술부채 관리대장)

> **Architectural Classification Update**: This ledger is organized by architectural domain to align with the system's core design principles (`ARCH_*.md`). Resolved debts are purged after each sprint.

## 🏛️ 1. AGENTS & POPULATIONS (`ARCH_AGENTS.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-006 | 2026-02-02 | Static Personality (Deterministic Class Caste) | Adaptability loss; ignores economic context | **RESOLVED** |
| TD-162 | 2026-01-30 | Bloated God Class: Household (977 lines) | SRP violation; property delegation bloat | **ACTIVE** |
| TD-180 | 2026-02-01 | TestFile Bloat: `test_firm_decision_engine_new.py` | 828 lines; indicator of complex engine surface | **WARNING** |

## 🏭 2. FIRMS & CORPORATE

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-005 | 2026-01-12 | Hardcoded Halo Effect (Unfair hiring advantage) | Violates Market fairness; Redundant with BrandManager | **ACTIVE (LIQUIDATE)** |
| TD-073 | 2026-01-20 | Firm "Split Brain" (Stateful vs Stateless/DTO) | AI Training Impossibility; Cognitive Dissonance | **ACTIVE (P0)** |
| TD-190 | 2026-02-01 | Complex `if/elif` chain in `_execute_internal_order` | `firms.py` implementation complexity | **ACTIVE** |

## 🧠 3. DECISION & AI ENGINE (`ARCH_AI_ENGINE.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| (Empty) | | | | |

## 💹 4. MARKETS & ECONOMICS

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| (Empty) | | | | |

## 💸 5. SYSTEMS & TRANSACTIONS (`ARCH_TRANSACTIONS.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| (Empty) | | | | |

## 📦 6. DATA & DTO CONTRACTS

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| **HousingRefactor** | 2026-01-31 | Orphaned Housing Logic (Mortgage Bypass) | **CRITICAL** | **ACTIVE** | Housing market functional failure. |
| TD-065 | 2026-01-31 | Duplicated Housing Decision Logic | Maintenance Risk | **ACTIVE** | Consolidated housing logic pending. |

## 🧱 7. INFRASTRUCTURE & TESTING

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-122 | 2026-01-26 | Test Directory Fragmentation | Maintenance overhead; Writing friction | **ACTIVE (GRADUAL)** |
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
