# Technical Debt Ledger (기술부채 관리대장)

## 🔴 BLOCKER (진행 불가 - 즉시 해결 필요)

| ID | Date | Description | Impact | Status |
|---|---|---|---|---|
| TD-024 | 2026-01-15 | `pytest` 실행 시 테스트 경로 오류 | Phase 26 착수 불가 (테스트 신뢰성 훼손) | **BLOCKER** |

## 🟡 DEFERRED (Phase 27+ 상환 예정)

| ID | Date | Description | Remediation Plan | Impact | Status |
|---|---|---|---|---|---|
| TD-005 | 2026-01-12 | Hardcoded Halo Effect in `firms.py` | Implementation of dynamic "Interview" system | Marginal Product of Labor 이론 위배 | **DEFERRED** |
| TD-006 | 2026-01-12 | Deterministic Class Caste (`core_agents.py`) | Dynamic Education Market implementation | Agency 상실 및 Class 고착화 강제 | **DEFERRED** |
| TD-007 | 2026-01-12 | Industrial Revolution Stress Test Config | Natural Equilibrium Config Tuning | 비현실적 경제 상태 (무한 수요) | **DEFERRED** |
| TD-008 | 2026-01-14 | Primitive Valuation Logic in CPR | Implement Altman Z-Score solvency check | Inefficient CPR (Zombie Firms) | **DESIGNED** (P26.5) |
| TD-009 | 2026-01-14 | CPR Bailouts are Unconditional Grants | Convert to Interest-bearing Loans/Bonds | Lack of Fiscal Consequence | **DESIGNED** (P26.5) |
| TD-032 | 2026-01-15 | Fixed M&A Threshold (0.7) | Dynamic market-driven valuation | Rigid corporate consolidation | **DEFERRED** |
| TD-033 | 2026-01-15 | Static Wage Decay Rate (0.02) | Desperation-based adaptive decay | Linear unemployment expectations | **DEFERRED** |
| TD-034 | 2026-01-15 | Arbitrary Startup Cost (30000.0) | Capital market derived entry cost | Static barrier to entry | **DEFERRED** |
| TD-035 | 2026-01-15 | Fixed Tax Brackets (Static Multiples) | Policy-driven flexible brackets | Fiscal policy rigidity | **DEFERRED** |
| TD-036 | 2026-01-15 | Rigid Housing Review Cycle (30 Ticks) | Event-driven housing decisions | Deterministic mobility | **DEFERRED** |
| TD-037 | 2026-01-15 | Fixed PER Multiplier (10.0) | Sector-specific market derived PER | Generic firm valuation | **DEFERRED** |
| TD-038 | 2026-01-15 | Magic Numbers in R&D Logic (0.2, 100.0) | S-curve based R&D model | Linearized innovation | **DEFERRED** |
| TD-039 | 2026-01-15 | Linear Aging Mortality Formula | Quality-of-life weighted mortality | Demographic predictability | **DEFERRED** |
| TD-040 | 2026-01-15 | Fixed Immigration Trigger (U-rate 5%) | Policy-lever based immigration | Lack of demographic control | **DEFERRED** |
| TD-041 | 2026-01-15 | Constant M&A Success Prob (0.6) | Premium & Health based probability | Unrealistic takeover dynamics | **DEFERRED** |
| TD-042 | 2026-01-15 | Rigid AI State Thresholds (e.g. 1%) | Learned or continuous state space | Rule-based AI perception | **DEFERRED** |

---

## ✅ Resolved Debts (해결된 부채)

| ID | 발생일 | 해결일 | 부채 내용 | 해결 방법 |
|---|---|---|---|---|
| TD-024 | 2026-01-15 | 2026-01-15 | `pytest` 실행 시 테스트 경로 오류 | Created `pytest.ini` & Removed sys.path hacks |
| TD-030 | 2026-01-15 | 2026-01-15 | Missing Fractional Reserve System | Implemented Fractional Reserve & Credit Creation (WO-064) |
| TD-010 | 2026-01-14 | 2026-01-15 | Government AI Sensory Lag | Implemented High-Fidelity Sensory Architecture (WO-066) |
| TD-025 | 2026-01-14 | 2026-01-15 | Tracker Blindness & Infra Gap | Implemented LKP Fallback (WO-066) |
| TD-031 | 2026-01-15 | 2026-01-15 | Systemic Money Leakage | Implemented Monetary Integrity & Suture (WO-065) |
| TD-028 | 2026-01-15 | 2026-01-15 | Bear Market Instruments | Marked Out of Scope (Wrong Project) |
| TD-029 | 2026-01-15 | 2026-01-15 | Price Discovery | Marked Out of Scope (Wrong Project) |

---

## 📝 가이드라인
1. 팀장이 Jules의 보고를 바탕으로 전략적으로 수용한 모든 기술부채를 여기에 등록합니다.
2. 상환 조건은 구체적이어야 합니다 (예: "다음 Phase 시작 시", "특정 기능 구현 시").
3. 정기적인 아키텍처 감사 시 이 부기표를 기준으로 상환 계획을 수립합니다.
