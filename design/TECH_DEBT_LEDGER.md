# Technical Debt Ledger (기술부채 관리대장)

## 🟡 DEFERRED (Phase 27+ 상환 예정)

| ID | Date | Description | Remediation Plan | Impact | Status |
|---|---|---|---|---|---|
| TD-005 | 2026-01-12 | Hardcoded Halo Effect in `firms.py` | Implementation of dynamic "Interview" system | Marginal Product of Labor 이론 위배 | **DEFERRED** |
| TD-006 | 2026-01-12 | Deterministic Class Caste (`core_agents.py`) | Dynamic Education Market implementation | Agency 상실 및 Class 고착화 강제 | **DEFERRED** |
| TD-007 | 2026-01-12 | Industrial Revolution Stress Test Config | Natural Equilibrium Config Tuning | 비현실적 경제 상태 (무한 수요) | **PENDING_IMPLEMENTATION** (Phase 28) |
| TD-073 | 2026-01-20 | Firm Component State Ownership | Transfer data ownership (assets, employees) from Firm to specialized departments | Architectural purity | **DEFERRED** (Phase D) |

---

## 🔴 ACTIVE (즉시 상환 필요)

| ID | Date | Description | Remediation Plan | Impact | Status |
|---|---|---|---|---|---|
| **TD-103** | 2026-01-23 | **Leaky AI Abstraction (self-sharing)** | Refactor `DecisionContext` to accept DTOs strictly | Encapsulation Break / Side-effects | **STRUCTURAL_RISK** |
| **TD-122** | 2026-01-26 | **Test Directory Organization** | Structure tests into unit/api/stress | Maintenance overhead | **DEFERRED** |
| **TD-132** | 2026-01-28 | **Hardcoded Government ID** | Dynamically resolve Government ID from WorldState | Registry Inconsistency Risk | **ACTIVE** |
| **TD-133** | 2026-01-28 | **Global Config Pollution** | Namespace scenario parameters under `config.scenario` | Config Conflict Risk | **ACTIVE** |
| **TD-134** | 2026-01-28 | **Scenario-Specific Branching** | Replace `is_phase23` checks with generic strategy flags | Code Complexity / Technical Debt | **ACTIVE** |

---

## ⚪ ABORTED / DEPRECATED (연구 중단)

| ID | Date | Description | Reason for Abort | Impact |
|---|---|---|---|---|
| TD-105 | 2026-01-23 | DLL Loading Failure (C++ Agent) | System environment constraints / Strategy change | Abandoning C++ Native path for now |

---

## ✅ Resolved Debts (해결된 부채)

| ID | Date | Description | Solution | Impact | Status |
|---|---|---|---|---|---|
| TD-102 | 2026-01-23 | Residual Evaporation (Inheritance Leak) | Residual Catch-all (WO-112) | Systemic Deflation / Float Leak | **RESOLVED** |
| TD-104 | 2026-01-23 | Bank Interface Ghosting | Formalize `IBankService` Protocol (WO-113) | Design-Impl Gap | **RESOLVED** |
| TD-085 | 2026-01-22 | Firm Decision Mutual Exclusivity | Sequential processing in Firm Engine | GDP Ceiling | **RESOLVED** |
| TD-086 | 2026-01-22 | AI Agent Infant Survival | Configurable Engine Selection | Demographic Arch | **RESOLVED** |
| TD-074 | 2026-01-21 | `main.py` & `config.py` corruption | Restore from Git history | Blocked system | **RESOLVED** |
| TD-075 | 2026-01-21 | `Household` Facade Bloat | Refactored via EconComponent delegation | Maintenance overhead | **RESOLVED** |
| TD-076 | 2026-01-21 | `ProductionDepartment.produce` Redundancy | Refactor TFP calculation | Code readability | **RESOLVED** |
| TD-105 | 2026-01-24 | Positive Drift (+320) | Fix Reflux atomic transfer (TD-105) | Zero-sum violation | **RESOLVED** |
| TD-106 | 2026-01-24 | Bankruptcy Money Leak | Link Bankruptcy to Settlement (TD-106) | Zero-sum violation | **RESOLVED** |
| TD-112 | 2026-01-25 | Inheritance Rounding | Integer distribution (TD-112) | System Crash | **RESOLVED** |
| TD-110 | 2026-01-24 | Phantom Tax Revenue | Enforce Settle->Record pattern (WO-120) | Budget analytics failure | **RESOLVED** |
| TD-119 | 2026-01-26 | Implicit IBankService | Formalize IBankService Protocol (WO-120) | Interface Consistency | **RESOLVED** |
| TD-111 | 2026-01-24 | Reflux Alchemy (M2 Inflation) | Exclude `RefluxSystem` balance from M2 calculation | Monetary Integrity | **RESOLVED** |
| TD-116 | 2026-01-26 | Inheritance Residual Evaporation | Integer Distribution (Core Track) | Zero-Sum Integrity | **RESOLVED** |
| TD-120 | 2026-01-27 | Refactor TransactionProcessor Tax Calls | TaxAgency Injection (Track Bravo) | Maintenance Risk | **RESOLVED** |
| TD-121 | 2026-01-26 | Newborn Money Leak (DOA) | Initial Needs Config Injection (WO-121) | Agent Viability | **RESOLVED** |
| TD-101 | 2026-01-27 | Shadow Economy (Direct Mutation) | Enforce `SettlementSystem` usage (WO-125) | Zero-sum violation | **RESOLVED** |
| TD-117 | 2026-01-27 | DTO-Only Decisions (Regression) | Enforce Purity Gate (WO-125) | Purity Gate Violation | **RESOLVED** |
| TD-123 | 2026-01-27 | God Class: `Household` | Decompose into Stateless Components (WO-123) | Maintenance Overhead | **RESOLVED** |
| TD-124 | 2026-01-27 | God Class: `TransactionProcessor` | Split into 6-Layer Architecture (WO-124) | Scalability Risk | **RESOLVED** |
| TD-126 | 2026-01-27 | Implicit Bank Protocol | Formalize `IBankService` (TD-126) | Design-Impl Gap | **RESOLVED** |
| TD-125 | 2026-01-27 | Non-atomic Transfer Sequences | Implement atomic bank/transaction blocks (WO-125) | Monetary Integrity | **RESOLVED** |
| TD-130 | 2026-01-28 | Reflux System (Dark Pools) | Operation Sacred Refactoring (Purge Reflux) | Monetary Integrity | **RESOLVED** |
| TD-131 | 2026-01-28 | Monolithic TickScheduler | Operation Sacred Refactoring (Decomposition) | Architectural Clarity | **RESOLVED** |

---

## 📅 REPAYMENT PLAN: "THE GREAT RESET" (Phase 24-26)

| Milestone | Target Debts | Objective | Tooling |
| :--- | :--- | :--- | :--- |
| **Step 1: Purity Guard** | TD-101, TD-102 | Create `SettlementSystem` to centralize all asset movements. | ✅ **DONE** (WO-112) |
| **Step 2: Abstraction Wall** | TD-103, TD-078 | Complete DTO-only conversion for all AI Decision Engines. | `gemini:verify` |
| **Step 3: Formal Registry** | TD-104, TD-084 | Formalize all module interfaces (Bank, Tax, Govt) as Protocols. | ✅ **DONE** (WO-113) |
| **Step 4: Structural Reset** | TD-123, TD-124 | Split God Classes (`Household`, `TransactionProcessor`). | ✅ **DONE** (WO-123, WO-124) |
| **Step 5: Normalize Sequence** | TD-106, TD-109 | Normalize Tick Sequence. | **PLANNED** (Phase 26) |
