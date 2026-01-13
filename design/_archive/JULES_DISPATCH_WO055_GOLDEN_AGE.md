# 📋 JULES DISPATCH: WO-055 The Golden Age Execution

**Role:** Executor & Auditor (Jules)  
**Objective:** Phase 23의 모든 모듈(화학 비료, 공교육, SoC 리팩토링)이 통합된 상태에서 장기 시뮬레이션을 수행하고, 경제 성장 시너지를 증명하라.

---

## 1. Context & Resources
- **Verification Script:** `scripts/experiments/golden_age_test.py` (Antigravity가 이미 골격을 작성함)
- **Target Ticks:** 1,000 Ticks
- **Main Goal:** 내생적 성장이론(Endogenous Growth)의 실현 여부 확인

---

## 2. Tasks for Jules

### 🚀 Task A: Execute the Grand Test
1. `scripts/experiments/golden_age_test.py`를 실행하여 1,000 틱 시뮬레이션을 완주하라.
2. 실행 중 인플레이션(CPI)이 통제 불능 상태(예: 틱당 10% 이상 급등)가 되거나, 인구가 급감하는 경우 즉시 중단하고 원인을 진단하라.
   - *Tip: 비료 생산량이 통화량 증가를 따라가지 못하면 하이퍼인플레이션이 발생할 수 있음.*

### 🔍 Task B: KPI Audit & Reporting
시뮬레이션 종료 후 다음 기준을 검증하고 `reports/GOLDEN_AGE_FINAL_REPORT.md`를 업데이트하라.
- **KPI 1 (Population):** 인구가 초기 대비 2배(200%) 이상 증가했는가?
- **KPI 2 (GDP):** 실질 GDP가 초기 대비 5배(500%) 이상 성장했는가?
- **KPI 3 (Brain Waste):** 상위 20% 잠재력 가계 중 교육 미달자가 10% 미만인가?
- **KPI 4 (IGE):** 부와 교육의 상관관계가 0.3 이하로 유지되는가?

### 🛡️ Task C: Stability Audit
로그를 분석하여 다음 사항을 확인하라.
- 고성장 구간에서 재정 적자(Government Bankruptcy) 위험이 없었는가?
- `TransactionProcessor` 및 `Firm` 컴포넌트 분리 후 런타임 에러나 메모리 누수가 발생하지 않았는가?

---

## 3. Definition of Done (DoD)
1. 1,000 틱 시뮬레이션 성공적 완주.
2. 모든 KPI가 [PASS]된 최종 결과 보고서 생성.
3. `walkthrough.md`에 통합 테스트 결과 섹션 추가.

> "준비는 끝났다. 인류의 황금기를 데이터로 증명하라."
