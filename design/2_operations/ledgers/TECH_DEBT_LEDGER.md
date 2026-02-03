# Technical Debt Ledger (기술부채 관리대장)

> **Architectural Classification Update**: This ledger is organized by architectural domain to align with the system's core design principles (`ARCH_*.md`). Resolved debts are purged after each sprint.

## 🏛️ 1. AGENTS & POPULATIONS (`ARCH_AGENTS.md`)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-180 | 2026-02-01 | TestFile Bloat: `test_firm_decision_engine_new.py` | 828 lines; indicator of complex engine surface | **WARNING** |

## 🏭 2. FIRMS & CORPORATE

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| (No Active Items) | | | | |

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
| TD-160 | 2026-02-02 | Non-Atomic Inheritance (Direct Asset Transfer) | Money leaks during death; Partial state corruption | **CRITICAL** |
| TD-187 | 2026-02-02 | Severance Pay Race Condition | Over-withdrawal during firm liquidation | **HIGH** |
| TD-187-DEBT | 2026-02-03 | Hardcoded Logic & Fragile State in Liquidation | `LiquidationManager` uses hardcoded `haircut` (20%) and directly manipulates `PublicManager` state (`.managed_inventory`), breaking encapsulation. | Refactoring |
| TD-192 | 2026-02-03 | Direct Asset Manipulation (_assets Bypassing SettlementSystem) | Zero-Sum breakage; Magic Money leaks | **CRITICAL** |

## 📦 6. DATA & DTO CONTRACTS

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-191 | 2026-02-03 | Weak Typing & DTO Contract Violation (Any Abuse) | Runtime errors; Maintenance nightmare | **HIGH** |

## 🧱 7. INFRASTRUCTURE & TESTING

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| (Empty) | | | | |

## 📜 8. OPERATIONS & DOCUMENTATION

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-150 | 2026-01-29 | Ledger Management Process | Loss of context | **ACTIVE** |
| TD-183 | 2026-02-01 | Sequence Deviation Documentation | Fast-Fail Liquidation needs ARCH entry | **ACTIVE** |
| TD-188 | 2026-02-01 | Inconsistent Config Path Doc | `PROJECT_STATUS.md` path mismatch | **ACTIVE** |
| TD-190 | 2026-02-03 | Magic Number Proliferation (Hardcoded Simulation Constants) | Hard to tune/test; Fragile logic | **MEDIUM** |
| TD-193 | 2026-02-03 | Fragmented Implementation: Half-baked Political System | Spec (Leviathan) vs Code (ruling_party) drift; logic duplication | **WARNING** |

---

## ⚪ ABORTED / DEPRECATED (연구 중단)

| ID | Date | Description | Reason for Abort | Impact |
|---|---|---|---|---|
| TD-105 | 2026-01-23 | DLL Loading Failure (C++ Agent) | System environment constraints | Abandoned C++ |
| TD-135-v1 | 2026-01-28 | Operation Abstraction Wall (Initial) | Failed due to 'Mock-Magic' leaks | Architectural Bloat |

---
