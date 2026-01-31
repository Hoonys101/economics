# Work Order: - Adaptive Equilibrium (The Invisible Hand v2)

**Phase:** 21.6
**Priority:** CRITICAL
**Date:** 2026-01-11
**Architect Prime Approval:** ✅ Approved with Refinements

---

## 1. Problem Statement

Track A (Reservation Wage 0.7)가 너무 강력하여 **"노동의 독재(84.88%)"** 발생.
노동자가 임금 거부 → 수입 없음 → 굶어 죽음 → 경제 붕괴.

**근본 원인:** System 1(생존 본능)이 결여된 채 System 2(계산된 협상)만 작동.

---

## 2. Objective

**적응형(Adaptive) 시스템으로 동적 균형(50-60%) 달성**

---

## 3. Parameters (Approved)

```python
# config.py - Phase 21.6 Revision
WAGE_DECAY_RATE = 0.02 # 실업 1틱당 희망임금 하락률 (2%)
WAGE_RECOVERY_RATE = 0.01 # 취업 시 희망임금 상승률 (1%)
RESERVATION_WAGE_FLOOR = 0.3 # 최저 희망임금 (시장 평균의 30%)
SURVIVAL_CRITICAL_TURNS = 5 # 생존 가능 잔여 기간 임계값
```

---

## 4. Implementation Plan

### Track A: Survival Override (생존 본능 주입)

**핵심 로직 변경:** "실업 5일차"가 아니라 **"잔고 기준 생존 가능 기간"**

```python
# Survival Trigger 계산
food_inventory = household.inventory.get("basic_food", 0)
food_price = market_data.get("basic_food", {}).get("avg_price", 10.0)
survival_days = food_inventory + (household.assets / food_price)

if survival_days < SURVIVAL_CRITICAL_TURNS:
 # Panic Mode: 어떤 임금이든 수락
 reservation_wage = 0 # Disable floor
```

**결과:** 자산가는 버티고, 빈곤층은 즉시 반응.

---

### Track B: Adaptive Reservation Wage (눈높이 유연화)

**Household에 `patience_counter` 또는 `wage_expectation_modifier` 추가:**

```python
# 매 틱 실업 상태일 때
if not household.is_employed:
 household.wage_modifier *= (1.0 - WAGE_DECAY_RATE)
 household.wage_modifier = max(RESERVATION_WAGE_FLOOR, household.wage_modifier)
else:
 # 취업 중이면 소폭 상승
 household.wage_modifier *= (1.0 + WAGE_RECOVERY_RATE)
 household.wage_modifier = min(1.0, household.wage_modifier) # Cap at 100%
```

**Final Reservation Wage:**
```python
final_reservation = market_avg_wage * household.wage_modifier
```

---

### Track C: Money Supply Bug Fix

**음수 자산 방지:**
```python
# Firm.update_needs 임금 지급 전
if firm.assets < wage:
 # Cannot pay - Zombie or Fire with severance
```

---

## 5. File Changes

| File | Change |
|---|---|
| `config.py` | 4개 파라미터 추가 |
| `simulation/core_agents.py` | Household에 `wage_modifier` 속성 추가 |
| `simulation/decisions/ai_driven_household_engine.py` | Survival Override + Adaptive Wage |
| `simulation/decisions/rule_based_household_engine.py` | 동일 로직 적용 |

---

## 6. Verification

```bash
python scripts/iron_test.py --ticks 100
```

**Success Criteria:**
- Labor Share: 30-70% (자연 수렴)
- Population: 안정 (대량 사망 없음)
- Money Supply: 양수 유지

---

## 7. Expected Outcome: Damped Oscillation

```
초기: 서로 눈치 보며 탐색 (진폭 큼)
중기: 실업자는 내리고, 기업은 올리며 교차 (Oscillation)
말기: 시장 균형점에서 안정화 (Convergence → 50-60%)
```
