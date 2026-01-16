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
| TD-007 | 2026-01-12 | Industrial Revolution Stress Test Config | Natural Equilibrium Config Tuning | 비현실적 경제 상태 (무한 수요) | **READY** (WO-077 Spec Done) |
| TD-008 | 2026-01-14 | Primitive Valuation Logic in CPR | Implement Altman Z-Score solvency check | Inefficient CPR (Zombie Firms) | **DESIGNED** (P26.5) |
| TD-009 | 2026-01-14 | CPR Bailouts are Unconditional Grants | Convert to Interest-bearing Loans/Bonds | Lack of Fiscal Consequence | **DESIGNED** (P26.5) |
| TD-032 | 2026-01-15 | `FinanceSystem` QE Violation | Central Bank must only purchase bonds if yield > 10% | Monetary integrity compromised | **RESOLVED** (WO-072) |
| TD-033 | 2026-01-15 | Bailout Loan Covenant Missing | Repayment from profit must be a senior covenant | Moral hazard for bailed-out firms | **RESOLVED** (WO-072) |
| TD-034 | 2026-01-15 | Hardcoded Debt Parameters | Bond maturity, risk premia must be config-driven | Reduced model configurability | **DEFERRED** |
| TD-035 | 2026-01-15 | Incorrect Startup Runway Check | Solvency check uses `assets` instead of `cash_reserve` | Inaccurate solvency assessment | **RESOLVED** (WO-072) |
| TD-036 | 2026-01-15 | Monetary Integrity Violation (Debt Service) | `service_debt` only pays principal, not interest | Creates money from thin air | **RESOLVED** (WO-072) |
| TD-037 | 2026-01-15 | Monetary Integrity Violation (QE) | QE creates money without CB balance sheet operation | Breaks zero-sum principle | **RESOLVED** (WO-072) |
| TD-038 | 2026-01-15 | Missing Bailout State Tracking | No flag to track if a firm `has_bailout_loan` | Inability to enforce covenants | **RESOLVED** (WO-072) |
| TD-039 | 2026-01-15 | SoC Violation (`DemographicManager`) | `DemographicManager` should not be aging firms | Blurs architectural boundaries | **RESOLVED** (WO-072) |
| TD-040 | 2026-01-15 | Fiscal Cliff Risk | Government spends money before confirming bond issuance | Potential for un-funded spending | **RESOLVED** (WO-072) |
| TD-041 | 2026-01-15 | Hardcoded Bailout Covenant Ratio | Repayment ratio of 0.5 is hardcoded | Reduced model configurability | **DEFERRED** |
| TD-042 | 2026-01-15 | Incomplete Test Suite | Major new `FinanceSystem` lacks dedicated unit tests | High risk of un-caught regressions | **RESOLVED** (WO-072) |
| TD-043 | 2026-01-16 | God Class: `Simulation` in `engine.py` | Decompose into specialized managers (Lifecycle, Initializer) | SoC Violation, maintenance risk | **RESOLVED** (WO-078) |
| TD-044 | 2026-01-16 | God Class: `Household` in `core_agents.py` | Refactor into components (Economy, Labor) | Tightly coupled state/logic | **READY** (Spec Done) |
| TD-045 | 2026-01-16 | God Class: `Firm` in `firms.py` | Deepen departmentalization (Production, Sales) | Production/Finance coupling | **RESOLVED** (TD-045 PR) |
| TD-046 | 2026-01-16 | Hardcoded Constants in SoC Components | Migrate `0.995`, `1.1`, `0.9`, `10.0`, `100.0` to config | Reduced configurability | **DEFERRED** (TD-007 시 일괄처리) |

---

## ✅ Resolved Debts (해결된 부채)

| ID | 발생일 | 해결일 | 부채 내용 | 해결 방법 |
|---|---|---|---|---|
| TD-024 | 2026-01-15 | 2026-01-15 | `pytest` 실행 시 테스트 경로 오류 | Created `pytest.ini` & Removed sys.path hacks |
| TD-030 | 2026-01-15 | 2026-01-15 | Missing Fractional Reserve System | Implemented Fractional Reserve & Credit Creation (WO-064) |
| TD-010 | 2026-01-14 | 2026-01-15 | Government AI Sensory Lag | Implemented High-Fidelity Sensory Architecture (WO-066) |
| TD-025 | 2026-01-14 | 2026-01-15 | Tracker Blindness & Infra Gap | Implemented LKP Fallback (WO-066) |
| TD-031 | 2026-01-15 | 2026-01-16 | Systemic Money Leakage in Finance | Implemented Atomic Protocol-based Transfer (WO-073) |
| TD-028 | 2026-01-15 | 2026-01-15 | Bear Market Instruments | Marked Out of Scope (Wrong Project) |
| TD-029 | 2026-01-15 | 2026-01-15 | Price Discovery | Marked Out of Scope (Wrong Project) |

---

## 📝 가이드라인
1. 팀장이 Jules의 보고를 바탕으로 전략적으로 수용한 모든 기술부채를 여기에 등록합니다.
2. 상환 조건은 구체적이어야 합니다 (예: "다음 Phase 시작 시", "특정 기능 구현 시").
3. 정기적인 아키텍처 감사 시 이 부기표를 기준으로 상환 계획을 수립합니다.
