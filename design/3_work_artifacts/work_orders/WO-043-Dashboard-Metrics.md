# Work Order: - Dashboard Metric Expansion

**Phase:** 21.5-Revision (Stabilization)
**Priority:** HIGH
**Date:** 2026-01-11
**Architect Prime Directive:** Phase 22 진입 중단. 정상 경제 파라미터 복원 우선.

---

## 1. Problem Statement

현재 노동분배율이 **4.7%** (정상: ~60%)로 기형적 상태.
원인: Cobb-Douglas 생산함수의 α(노동 탄력성) 파라미터 불균형.

**대시보드 진단 기능 부재:**
- 노동분배율 그래프 ❌
- 화폐 유통속도 ❌
- 재고 회전율 ❌

---

## 2. Objective

**"돈이 왜 안 도는지"를 눈으로 볼 수 있게 만든다.**

---

## 3. Deliverables

### Step 1: Dashboard Metric Expansion

| Metric | 공식 | 정상 범위 | 파일 |
|---|---|---|---|
| **Labor Share** | `총 임금 / GDP` | 50-70% | `dashboard/app.py` |
| **Velocity of Money** | `GDP / M1` | 1.5-3.0 | `dashboard/app.py` |
| **Inventory Turnover** | `판매량 / 평균 재고` | 4-8 | `dashboard/app.py` |

### Step 2: Tracker 보강

| Indicator | Source | 추가 위치 |
|---|---|---|
| `total_labor_income` | `Firm.update_needs` 집계 | `simulation/tracker.py` |
| `money_velocity` | `GDP / money_supply` | `simulation/tracker.py` |
| `inventory_turnover` | `sales_volume / avg_inventory` | `simulation/tracker.py` |

### Step 3: Config 파라미터 추가

```python
# config.py
LABOR_ELASTICITY_MIN = 0.3 # α 하한선 (노동분배율 30% 보장)
AUTOMATION_COST_MULTIPLIER = 2.0 # 자동화 비용 증가
KICKSTART_INVENTORY = 100.0 # 초기 재고량 증가
```

---

## 4. Implementation Plan

### Track A: Dashboard UI (Jules-Dashboard)

1. `dashboard/app.py`에 **Labor Share** 시계열 차트 추가
2. `dashboard/app.py`에 **Velocity of Money** 차트 추가
3. `dashboard/app.py`에 **Inventory Turnover** 차트 추가

### Track B: Tracker Logic (Jules-Backend)

1. `simulation/tracker.py` - `track_labor_share()` 메서드 추가
2. `simulation/tracker.py` - `track_velocity()` 메서드 추가
3. `simulation/engine.py` - Tracker 호출 통합

---

## 5. Verification

1. Dashboard에서 3개 신규 차트 확인
2. Iron Test 실행 → 그래프에 실시간 데이터 반영 확인
3. 노동분배율 파라미터 조정 → 그래프 변화 확인

---

## 6. Success Criteria

| Metric | Before | Target |
|---|---|---|
| Labor Share Visibility | ❌ Log only | ✅ Dashboard Chart |
| Labor Share Value | 4.7% | **50-60%** |
| Unemployment | 70%+ | **5-15%** |

---

## 7. Jules Assignment

| Track | Assignee | Task |
|---|---|---|
| **Track A** | Jules-A | Dashboard UI (3 charts) |
| **Track B** | Jules-B | Tracker Logic (metrics) |

**병렬화 가능:** 두 트랙 동시 진행.
