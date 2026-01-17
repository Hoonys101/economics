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
| TD-007 | 2026-01-12 | Industrial Revolution Stress Test Config | Natural Equilibrium Config Tuning | 비현실적 경제 상태 (무한 수요) | **IMPLEMENTING** (WO-079) |
| TD-034 | 2026-01-15 | Hardcoded Debt Parameters | Bond maturity, risk premia must be config-driven | Reduced model configurability | **DEFERRED** |
| TD-041 | 2026-01-15 | Hardcoded Bailout Covenant Ratio | Repayment ratio of 0.5 is hardcoded | Reduced model configurability | **DEFERRED** |
| TD-046 | 2026-01-16 | Hardcoded Constants in SoC Components | Migrate constants to config system | Reduced configurability | **IN_PROGRESS** (WO-079 통합 진행) |

| TD-043 | 2026-01-16 | God Class: `Simulation` in `engine.py` | SoC Refactoring (Wait for WO-Soc-2) | High Coupling, Low Maintainability | **REOPENED** (SoC Failed/Partial) |
| TD-044 | 2026-01-16 | God Class: `Household` in `core_agents.py` | SoC Refactoring (Wait for WO-Soc-2) | High Coupling, Low Maintainability | **REOPENED** (SoC Failed/Partial) |
| TD-045 | 2026-01-16 | God Class: `Firm` in `firms.py` | SoC Refactoring (Wait for WO-Soc-2) | High Coupling, Low Maintainability | **REOPENED** (SoC Failed/Partial) |

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
| TD-008 | 2026-01-14 | 2026-01-17 | Primitive Valuation Logic in CPR | Implemented Altman Z-Score (TD-008) |
| TD-009 | 2026-01-14 | 2026-01-17 | CPR Bailouts are Unconditional Grants | Implemented Bailout Loans (TD-008) |
| TD-028 | 2026-01-15 | 2026-01-15 | Bear Market Instruments | Marked Out of Scope |
| TD-029 | 2026-01-15 | 2026-01-15 | Price Discovery | Marked Out of Scope |
| TD-048 | 2026-01-16 | 2026-01-17 | Environment Instability | Pinned `requirements.txt` versions (TD-048) |


---

## 📝 가이드라인
1. 팀장이 Jules의 보고를 바탕으로 전략적으로 수용한 모든 기술부채를 여기에 등록합니다.
2. 상환 조건은 구체적이어야 합니다 (예: "다음 Phase 시작 시", "특정 기능 구현 시").
3. 정기적인 아키텍처 감사 시 이 부기표를 기준으로 상환 계획을 수립합니다.
