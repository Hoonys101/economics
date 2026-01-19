# Technical Debt Ledger (기술부채 관리대장)

## 🔴 BLOCKER (진행 불가 - 즉시 해결 필요)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| - | - | 현재 블로커 없음 | - | - |

## 🟡 DEFERRED (Phase 27+ 상환 예정)

| ID | Date | Description | Remediation Plan | Impact | Status |
|---|---|---|---|---|---|
| TD-005 | 2026-01-12 | Hardcoded Halo Effect in `firms.py` | Implementation of dynamic "Interview" system | Marginal Product of Labor 이론 위배 | **DEFERRED** |
| TD-006 | 2026-01-12 | Deterministic Class Caste (`core_agents.py`) | Dynamic Education Market implementation | Agency 상실 및 Class 고착화 강제 | **DEFERRED** |
| TD-007 | 2026-01-12 | Industrial Revolution Stress Test Config | Natural Equilibrium Config Tuning | 비현실적 경제 상태 (무한 수요) | **PENDING_IMPLEMENTATION** (Phase 28) |
| TD-034 | 2026-01-15 | Hardcoded Debt Parameters | Bond maturity, risk premia must be config-driven | Reduced model configurability | **DEFERRED** |
| TD-041 | 2026-01-15 | Hardcoded Bailout Covenant Ratio | Repayment ratio of 0.5 is hardcoded | Reduced model configurability | **DEFERRED** |
| TD-050 | 2026-01-17 | Observer Scanner Path Inclusion | Exclude `scripts/observer` from scan loop | False positives in complexity reports | **DEFERRED** |
| TD-051 | 2026-01-17 | Documentation Placeholders | Replace `WO-XXX` with actual IDs in manuals | Confusion in developer onboarding | **DEFERRED** |
| TD-058 | 2026-01-19 | `FinanceSystem` - `Firm` Tight Coupling | Introduce `FinancialStatementDTO` in `Firm` | Architecture Rigidity / Brittle Tests | **RESOLVED** (Phase 29) |
| TD-059 | 2026-01-19 | Legacy Logic in `FinanceDepartment` | Refactor component to use `AltmanZScoreCalculator` | Logic Duplication / SSOT Violation | **DEFERRED** |
| TD-060 | 2026-01-19 | Hardcoded Scenario Path in `Initializer` | Implement dynamic lookup in `ConfigManager` | Low Configurability / Brittle Tests | **RESOLVED** (Phase 29) |
| TD-061 | 2026-01-19 | Mock Fragility in Stress Testing | Collect 'Golden Data' and implement typed mocks | Brittle Tests / High Dev Friction | **IN_PROGRESS** (WO-080) |
| TD-063 | 2026-01-19 | `sys.path` Manipulation in Scripts | Use `pathlib` for stable project root detection | Unpredictable Import Behavior | **DEFERRED** |
| TD-064 | 2026-01-20 | `Household.age` Setter Missing | Implement setter in `Household` or use `DemographicsComponent` directly | `AttributeError` crashing simulation | **OPEN** |
| TD-065 | 2026-01-20 | God Class `Household` (1k+ LOC) | Refactor into Components (`Bio`, `Econ`, `Social`) | High Coupling, Difficult Testing | **OPEN** |
| TD-066 | 2026-01-20 | God Class `Simulation` (900+ LOC) | Decompose into `Runner`, `WorldState`, `TickScheduler` | SRP Violation, Hard to Extend engine | **OPEN** |
| TD-067 | 2026-01-20 | God Class `Firm` Wrapper Bloat | Remove wrapper properties, use explicit sub-components (`hr`, `finance`) | Code Duplication, Maintenance Burden | **OPEN** |
| TD-068 | 2026-01-20 | Observer Scans `design/` Artifacts | Exclude `design/` from `scan_codebase.py` | False Positives in Health Report | **OPEN** |
| TD-069 | 2026-01-20 | Doc Placeholders (`WO-XXX`) | Replace placeholders with actual Process/IDs in Manuals | Confusing Documentation | **OPEN** |



---

## ✅ Resolved Debts (해결된 부채)

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


---

## 📝 가이드라인
1. 팀장이 Jules의 보고를 바탕으로 전략적으로 수용한 모든 기술부채를 여기에 등록합니다.
2. 상환 조건은 구체적이어야 합니다 (예: "다음 Phase 시작 시", "특정 기능 구현 시").
3. 정기적인 아키텍처 감사 시 이 부기표를 기준으로 상환 계획을 수립합니다.
