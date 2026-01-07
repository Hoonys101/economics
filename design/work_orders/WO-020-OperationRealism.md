# WO-020: Operation "Realism" - Economic Stability Fix

## 1. Background
1000틱 시뮬레이션 결과, 경제가 **"정지(GDP=0)"** 상태에 도달했습니다. 분석 결과 두 가지 근본 원인이 발견되었습니다:
1.  **물리적 고장 (Leak)**: 정부 지출이 자산을 초과하면서 허공에서 화폐가 생성됨.
2.  **심리적 고장 (Stagnation)**: 돈이 가계/은행에 고여 순환하지 않음 (유동성 함정).

## 2. Objectives
- [ ] **Fix Leak**: 정부 자산이 **절대 음수가 되지 않도록** 하드 제약 추가.
- [ ] **Audit**: 1000틱 종료 시 **"부문별 화폐 보유량(Pie Chart)"** 시각화.
- [ ] **No Free Lunch**: 조건 없는 복지 축소 및 기아 메커니즘 강화.

---

## 3. Detailed Tasks

### 3.1 Fix Leak: Government Spending Hard Constraint
**File**: `simulation/agents/government.py`

**현재 문제 (예상)**:
```python
# 현재 코드 (예상)
self.assets -= expenditure  # 잔고가 부족해도 그냥 차감 -> 음수 발생 -> 화폐 생성
```

**수정안**:
```python
# In provide_subsidy() or any spending method:
actual_spend = min(planned_spend, max(0.0, self.assets))
if actual_spend < planned_spend:
    logger.warning(f"SPENDING_CAPPED | Requested: {planned_spend:.2f}, Actual: {actual_spend:.2f}")
self.assets -= actual_spend
# ... rest of logic uses actual_spend instead of planned_spend
```
- `provide_subsidy`, `invest_infrastructure`, `run_welfare_check` 등 모든 지출 메서드에 적용.
- `self.assets < 0` 상태가 절대 발생하지 않도록 보장.

### 3.2 Audit: Money Distribution Pie Chart
**File**: `scripts/visualize_economy.py` (수정)

1000틱 종료 시, 아래 4개 부문의 화폐 보유량을 계산하여 **Pie Chart**로 시각화:
- **Households**: `SUM(agent_states.assets WHERE agent_type='household')`
- **Firms**: `SUM(agent_states.assets WHERE agent_type='firm')`
- **Government**: `fiscal_history.json` 마지막 `assets` 값
- **Bank**: `bank_agents.assets` (또는 해당 데이터 로드)

파일명: `reports/figures/money_distribution.png`

### 3.3 No Free Lunch: Welfare Reform
**File**: `simulation/agents/government.py` or `simulation/engine.py`

#### 3.3.1 조건부 복지 (Workfare)
- 현재: "실업자이면 복지 지급"
- 수정: "실업자 + **이번 틱에 노동 매도 주문(Labor Sell Order)을 제출한 경우**에만 지급"
- 즉, "구직 활동" 없이 복지만 받는 것을 막음.

#### 3.3.2 기아 메커니즘 강화
- 현재 `SURVIVAL_NEED_DEATH_THRESHOLD`가 너무 관대하지 않은지 검토.
- If `household.assets == 0 AND household.inventory["basic_food"] == 0` $\rightarrow$ Death within N ticks.
- 가계가 **진짜로 굶어 죽을 수 있어야** 노동 공급 곡선이 정상화됨.

---

## 4. Verification
- [ ] 100틱 시뮬레이션 후 `government.assets >= 0` 확인.
- [ ] `reports/figures/money_distribution.png` 생성 확인.
- [ ] 복지 개혁 후 가계 생존율이 100% 미만인지 확인 (자연 도태 발생 여부).

## 5. Success Criteria
- **Engine Delta = 0.0000** (화폐 누수 Zero)
- **GDP > 0** at Tick 1000 (경제 가동 유지)
- 부문별 화폐 파이 차트에서 **한 쪽에 100% 몰리지 않음** (건전한 순환)
