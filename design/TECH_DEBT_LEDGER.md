# Technical Debt Ledger (기술부채 관리대장)


## 🟡 DEFERRED (Phase 27+ 상환 예정)

| ID | Date | Description | Remediation Plan | Impact | Status |
|---|---|---|---|---|---|
| TD-005 | 2026-01-12 | Hardcoded Halo Effect in `firms.py` | Implementation of dynamic "Interview" system | Marginal Product of Labor 이론 위배 | **DEFERRED** |
| TD-006 | 2026-01-12 | Deterministic Class Caste (`core_agents.py`) | Dynamic Education Market implementation | Agency 상실 및 Class 고착화 강제 | **DEFERRED** |
| TD-007 | 2026-01-12 | Industrial Revolution Stress Test Config | Natural Equilibrium Config Tuning | 비현실적 경제 상태 (무한 수요) | **PENDING_IMPLEMENTATION** (Phase 28) |
| TD-074 | 2026-01-21 | `main.py` & `config.py` corruption | Restore from Git history + Add Merge Guard | Blocked system execution | **RESOLVED** |
| TD-075 | 2026-01-21 | `Household` Facade Bloat (850+ lines) | Refactored via EconComponent delegation (WO-092) | Maintenance overhead | **RESOLVED** |
| TD-076 | 2026-01-21 | `ProductionDepartment.produce` Redundancy | Refactor TFP calculation to avoid double multiplier check | Code readability | **RESOLVED** (WO-105) |
| TD-077 | 2026-01-21 | `EconComponent` Hardcoded Price History Maxlen | Move `maxlen=10` to global configuration | Configuration Gap | **RESOLVED** (WO-105) |
| TD-104 | 2026-01-21 | Legacy `SimpleNamespace` in `fixture_harvester.py` | Enforce `GoldenLoader` and move to `simulation/utils/` | SoC Violation | **RESOLVED** (WO-105) |
| TD-078 | 2026-01-22 | `DecisionContext` Leaky Abstraction | Mandatory DTO-only snapshots for all engines | Integrity Risk | **PENDING** |
| TD-079 | 2026-01-22 | `TickScheduler` God Class Bloat | Decompose into `Orchestrator` and `Activator` | Maintainability | **PENDING** |
| TD-084 | 2026-01-22 | DTO Schema Gap vs Specs | Expand DTO fields to include all macro indicators | Data Inconsistency | **PENDING** |


---

## ✅ Resolved Debts (해결된 부채)
| ID | Date | Description | Solution | Impact | Status |
|---|---|---|---|---|---|
| TD-085 | 2026-01-22 | Firm Decision Mutual Exclusivity | Sequential processing in Firm Engine | GDP Ceiling | **RESOLVED** |
| TD-086 | 2026-01-22 | AI Agent Infant Survival | Configurable Engine Selection (Mainstreamed) | Demographic Arch | **RESOLVED** |
| TD-065 | 2026-01-20 | God Class `Household` Refactoring | Decomposed into `Bio`, `Econ`, `Social` components + Facade | High Coupling | **RESOLVED** (PR Merged) |
| TD-066 | 2026-01-20 | God Class `Simulation` Refactoring | Decomposed into `WorldState`, `TickScheduler`, `ActionProcessor` | SRP Violation | **RESOLVED** (PR Merged) |
| TD-069 | 2026-01-20 | Doc Placeholders (`WO-XXX`) | Replaced with concrete examples in Manuals | Confusing Documentation | **RESOLVED** (Direct) |
| TD-071 | 2026-01-20 | Magic Number in `verify_inheritance.py` | Used `self.heir.id` dynamic reference | Code Smell | **RESOLVED** (Direct) |
| TD-067 | 2026-01-20 | God Class `Firm` Wrapper Bloat | Removed wrapper properties, encapsulated CorporateManager interactions | High Coupling | [RESOLVED] |
| TD-073 | 2026-01-20 | Firm Component State Ownership | Transfer data ownership (assets, employees) from Firm to specialized departments | Architectural purity / Leaky abstractions | **DEFERRED** (Phase D) |
| TD-072 | 2026-01-20 | Test Framework Inconsistency | Migrated `unittest` to `pytest` in `test_government` and `verify_vanity_society` | Maint. Overhead | **RESOLVED** (Direct) |
| TD-058 | 2026-01-20 | `FinanceSystem` - `Firm` Tight Coupling | Introduced `FinancialStatementDTO` | High Coupling | **RESOLVED** (Phase 29/WO-084) |
| TD-059 | 2026-01-20 | Legacy Logic in `FinanceDepartment` | Delegated to `AltmanZScoreCalculator` | SRP Violation | **RESOLVED** (WO-084) |
| TD-063 | 2026-01-20 | `sys.path` Manipulation in Scripts | Normalized using `pathlib` | Brittle Imports | **RESOLVED** (Infra-Cleanup) |
| TD-050 | 2026-01-20 | Observer Scanner Path Inclusion | Excluded `observer/` and `design/` | Report Noise | **RESOLVED** (Infra-Cleanup) |
| TD-051 | 2026-01-20 | Documentation Placeholders | Fixed `WO-XXX` placeholders | Poor Meta-Data | **RESOLVED** (Infra-Cleanup) |
| TD-034 | 2026-01-20 | Hardcoded Debt Parameters | Moved to `economy_params.yaml` | Configurability Gap | **RESOLVED** (Finance-Config) |
| TD-041 | 2026-01-20 | Hardcoded Bailout Covenant Ratio | Moved to `economy_params.yaml` | Configurability Gap | **RESOLVED** (Finance-Config) |

| ID | 발생일 | 해결일 | 부채 내용 | 해결 방법 |
|---|---|---|---|---|
| TD-024 | 2026-01-15 | 2026-01-15 | `pytest` 실행 시 테스트 경로 오류 | Created `pytest.ini` & Removed sys.path hacks |
| TD-030 | 2026-01-15 | 2026-01-15 | Missing Fractional Reserve System | Implemented Fractional Reserve & Credit Creation (WO-064) |
| TD-010 | 2026-01-14 | 2026-01-15 | Government AI Sensory Lag | Implemented High-Fidelity Sensory Architecture (WO-066) |
| TD-025 | 2026-01-14 | 2026-01-15 | Tracker Blindness & Infra Gap | Implemented LKP Fallback (WO-066) |
| TD-031 | 2026-01-15 | 2026-01-16 | Systemic Money Leakage in Finance | Implemented Atomic Protocol-based Transfer (WO-073) |
| TD-047 | 2026-01-16 | 2026-01-16 | Startup Crash: Household Generation Attribute | Fixed via `try/except` in `BaseAgent` |
| TD-032~042 | 2026-01-15 | 2026-01-16 | Finance System Flaws (QE, Bailouts, etc.) | Resolved via WO-072/073 |
| TD-008 | 2026-01-14 | 2026-01-19 | Primitive Valuation Logic in CPR | Implemented Domain-driven Altman Z-Score |
| TD-009 | 2026-01-14 | 2026-01-17 | CPR Bailouts are Unconditional Grants | Implemented Bailout Loans (TD-008) |
| TD-028 | 2026-01-15 | 2026-01-15 | Bear Market Instruments | Marked Out of Scope |
| TD-029 | 2026-01-15 | 2026-01-15 | Price Discovery | Marked Out of Scope |
| TD-048 | 2026-01-16 | 2026-01-17 | Environment Instability | Pinned `requirements.txt` versions (TD-048) |
| TD-043 | 2026-01-16 | 2026-01-18 | God Class: `Simulation` | Extracted Systems (Social, Event, Commerce, Sensory) |
| TD-044 | 2026-01-16 | 2026-01-18 | God Class: `Household` | Extracted Components (AgentLifecycle, Market) |
| TD-045 | 2026-01-16 | 2026-01-18 | God Class: `Firm` | Implemented ILearningAgent support |
| TD-046 | 2026-01-16 | 2026-01-18 | Hardcoded Constants in SoC Components | Migrated to config system (WO-079) |
| TD-049 | 2026-01-18 | 2026-01-18 | Test Flakiness (ConfigManager Mocking) | Fixed via `side_effect` for default values |
| TD-070 | 2026-01-20 | 2026-01-20 | `test_rd_logic` coverage gap | Restored assertions in `test_corporate_manager.py` |
| TD-068 | 2026-01-20 | 2026-01-20 | Observer scans `design/` | Added `design` to `IGNORE_DIRS` in `scan_codebase.py` |
| TD-085 | 2026-01-22 | 2026-01-23 | Audit v2 Expansion: Sequential Pipeline | Verified implementation in 3 agents |
| TD-086 | 2026-01-22 | 2026-01-23 | Audit v2 Expansion: Newborn Engine | Verified implementation in DemographicManager |

---

## 🔴 ACTIVE (즉시 상환 필요 - Phase 26.5 연동)

| ID | Date | Description | Remediation Plan | Impact | Status |
|---|---|---|---|---|---|
| **TD-101** | 2026-01-23 | **Shadow Economy (Direct Mutation)** | Implement `FinanceSystem.atomic_transfer` and ban `assets +=` | Zero-sum violation / Audit blindness | **HIGH_PRIORITY** |
| **TD-102** | 2026-01-23 | **Residual Evaporation (Inheritance Leak)** | Implement Remainder Tracking in `InheritanceManager` | Systemic Deflation / Float Leak | **ACTUAL_LEAK** |
| **TD-103** | 2026-01-23 | **Leaky AI Abstraction (self-sharing)** | Refactor `DecisionContext` to accept DTOs strictly | Encapsulation Break / Side-effects | **STRUCTURAL_RISK** |
| **TD-104** | 2026-01-23 | **Bank Interface Ghosting** | Formalize `IBankService` Protocol in `modules/finance/api.py` | Implementation/Design Gap | **PARITY_ERROR** |

---

## 📅 REPAYMENT PLAN: "THE GREAT RESET" (Phase 24-26)

| Milestone | Target Debts | Objective | Tooling |
| :--- | :--- | :--- | :--- |
| **Step 1: Purity Guard** | TD-101, TD-102 | Create `SettlementSystem` to centralize all asset movements. Fix float residuals. | `gemini:spec` -> `jules:create` |
| **Step 2: Abstraction Wall** | TD-103, TD-078 | Complete DTO-only conversion for all AI Decision Engines. Remove `self` sharing. | `gemini:verify` |
| **Step 3: Formal Registry** | TD-104, TD-084 | Formalize all module interfaces (Bank, Tax, Govt) as Protocols. | `jules:create` |


---

## 📝 가이드라인
1. 팀장이 Jules의 보고를 바탕으로 전략적으로 수용한 모든 기술부채를 여기에 등록합니다.
2. 상환 조건은 구체적이어야 합니다 (예: "다음 Phase 시작 시", "특정 기능 구현 시").
3. 정기적인 아키텍처 감사 시 이 부기표를 기준으로 상환 계획을 상환합니다.
