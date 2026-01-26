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
| **TD-107** | 2026-01-23 | **Leaky Abstraction (HR Back-ref & Demeter)** | Remove back-references from components to DecisionContext | High Coupling | **STRUCTURAL_RISK** |
| **TD-108** | 2026-01-23 | **Stateful Engine Violation (Market & Govt Injection)** | Inject markets and GovernmentStateDTO via DecisionContext | Purity Gate Violation | **STRUCTURAL_RISK** |
| **TD-109** | 2026-01-23 | **Sacred Sequence Violation** | Move asset transfers (taxes, profit, infra) into Transaction Phase | Atomicity / Integration Risk | **PARTIALLY_RESOLVED** (Pending Fix) |
| **TD-111** | 2026-01-24 | **Reflux Alchemy (M2 Inflation)** | Exclude `RefluxSystem` balance from M2 calculation | Monetary Integrity | **ECONOMIC_RISK** |
| **TD-113** | 2026-01-24 | **Non-atomic Transfer Fallbacks** | Remove legacy `withdraw/deposit` fallbacks in `TransactionProcessor` | Asset destruction risk | **STRUCTURAL_RISK** |
| **TD-114** | 2026-01-25 | **Sparse System Tests** | Add tests for Housing, Education, etc. | Regression Risk | **STRUCTURAL_RISK** |
| **TD-115** | 2026-01-25 | **Tick 1 Financial Leak (-99,680)** | Identify source of 99k asset destruction at simulation start | Monetary Integrity | **CRITICAL** |
| **TD-116** | 2026-01-26 | **Inheritance Residual Evaporation** | Exact distribution with residue to last heir (math.floor) | Zero-Sum Integrity | **ACTIVE** |
| **TD-117** | 2026-01-26 | **Structural Purity: DTO-Only Decisions** | Replace live objects with MarketSnapshotDTO in make_decision | Purity Gate Violation | **ACTIVE** |
| **TD-118** | 2026-01-26 | **CommerceSystem Sequence Violation** | Split execution into 4-Phase integration in TickScheduler | Sacred Sequence Compliance| **ACTIVE** |
| **TD-120** | 2026-01-27 | **Refactor TransactionProcessor Tax Calls** | Inject TaxAgency; use atomic collection pattern | Maintenance Risk | **ACTIVE** |

---

## ⚪ ABORTED / DEPRECATED (연구 중단)

| ID | Date | Description | Reason for Abort | Impact |
|---|---|---|---|---|
| TD-105 | 2026-01-23 | DLL Loading Failure (C++ Agent) | System environment constraints / Strategy change | Abandoning C++ Native path for now |

---

## ✅ Resolved Debts (해결된 부채)

| ID | Date | Description | Solution | Impact | Status |
|---|---|---|---|---|---|
| TD-101 | 2026-01-23 | Shadow Economy (Direct Mutation) | SettlementSystem (WO-112) | Zero-sum violation | **RESOLVED** |
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

---

## 📅 REPAYMENT PLAN: "THE GREAT RESET" (Phase 24-26)

| Milestone | Target Debts | Objective | Tooling |
| :--- | :--- | :--- | :--- |
| **Step 1: Purity Guard** | TD-101, TD-102 | Create `SettlementSystem` to centralize all asset movements. | ✅ **DONE** (WO-112) |
| **Step 2: Abstraction Wall** | TD-103, TD-078 | Complete DTO-only conversion for all AI Decision Engines. | `gemini:verify` |
| **Step 3: Formal Registry** | TD-104, TD-084 | Formalize all module interfaces (Bank, Tax, Govt) as Protocols. | ✅ **DONE** (WO-113) |
| **Step 4: Structural Reset** | TD-106, TD-109 | Normalize Tick Sequence and Split God Classes. | **PLANNED** (Phase 26) |
