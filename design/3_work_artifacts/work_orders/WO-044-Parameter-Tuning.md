# Work Order: WO-044 - Parameter Tuning (노동분배율 정상화)

**Phase:** 21.5-Revision (Stabilization)
**Priority:** HIGH
**Date:** 2026-01-11
**Prerequisite:** WO-043 Complete ✅

---

## 1. Problem Statement

현재 노동분배율: **4.7%** (정상: ~60%)
원인: "지능의 비대칭" - Corporate AI가 최적화하여 노동 비용 0으로 수렴.

---

## 2. Objective

**Phase A 가드레일 적용으로 정상 경제 복원.**

---

## 3. Target Metrics

| Metric | Current | Target |
|---|---|---|
| Labor Share | 4.7% | **50-60%** |
| Unemployment | 70%+ | **5-15%** |
| Population | 유지 | 안정 성장 |

---

## 4. Guardrail Parameters

### Track A: Production Function 조정

```python
# config.py additions
LABOR_ELASTICITY_MIN = 0.3          # α 하한선 (30% 노동분배 보장)
MIN_WAGE_PRODUCTIVITY_LINK = 0.5    # 생산성 상승 시 임금 50% 연동
```

### Track B: 자동화 비용 증가

```python
AUTOMATION_TAX_RATE = 0.05          # 자동화 레벨당 5% 세금
AUTOMATION_COST_MULTIPLIER = 5.0    # 자동화 비용 5배
```

### Track C: 고용 안정성

```python
SEVERANCE_PAY_WEEKS = 4             # 해고 시 4주 퇴직금 강제
HIRING_FRICTION_COST = 50.0         # 채용 마찰 비용
```

---

## 5. Implementation Plan

### Step 1: Config 파라미터 추가
- `config.py`에 위 상수 추가

### Step 2: CorporateManager 수정
- `_manage_automation`: AUTOMATION_TAX 적용
- `_manage_hiring/_fire`: SEVERANCE_PAY 적용

### Step 3: Firm.produce 수정
- `alpha_adjusted`: LABOR_ELASTICITY_MIN 하한 적용

### Step 4: 검증
- Dashboard에서 Labor Share 그래프 확인
- Iron Test 재실행

---

## 6. Verification

```bash
streamlit run dashboard/app.py
python scripts/iron_test.py --ticks 100
```

**Success Criteria:**
- Labor Share > 30% (avg over 100 ticks)
- Unemployment < 30%
- No mass bankruptcy

---

## 7. Jules Assignment

| Track | Task | 파라미터 |
|---|---|---|
| **Track A** | Production Function 조정 | LABOR_ELASTICITY_MIN |
| **Track B** | Automation Cost 증가 | AUTOMATION_TAX_RATE |
| **Track C** | Severance Pay 도입 | SEVERANCE_PAY_WEEKS |

**병렬화 가능:** 3개 트랙 동시 진행.
