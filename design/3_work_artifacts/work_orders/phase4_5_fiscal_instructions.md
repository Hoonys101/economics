# W-2 Work Order: Operation "Phoenix Rising" (Phase 4.5 Hotfix)

> **Assignee**: Jules
> **Priority**: P0 (Emergency - Extinction Prevention)
> **Branch**: `feature/responsible-government`
> **Base**: `main`

---

## 📋 Overview
**문제**: 초기 자산(20,000)이 풍족해서 가계가 노동을 거부 → 기업 생산 중단 → Tick 50 전멸.
**해결**: 미시적(AI 결정) + 거시적(Config) 양면에서 **노동 공급**과 **시장 반응성**을 강화.

---

## ✅ Part A: Config Tuning (즉시 적용)
**File**: `config.py`

```python
# [SURVIVAL HOTFIX]
INITIAL_HOUSEHOLD_ASSETS_MEAN = 20000.0      # 유지 (충분한 초기 자금)
HOUSEHOLD_DEATH_TURNS_THRESHOLD = 10         # 유지 (굶어 죽기까지 유예)
INITIAL_FIRM_INVENTORY_MEAN = 50.0           # 신규 (Tick 1부터 식량 공급)

# [LABOR INCENTIVE]
WEALTH_THRESHOLD_FOR_LEISURE = 50000.0       # 신규 (20,000으로는 은퇴 불가)
SURVIVAL_PANIC_THRESHOLD = 80.0              # 신규 (이 이상이면 Panic Mode)
FOOD_SECURITY_DAYS = 3.0                     # 신규 (3일치 식량 미만이면 노동 강제)

# [DESPERATE HIRING]
DESPERATE_HIRING_WAGE_MULTIPLIER = 1.5       # 신규 (직원 0명이면 임금 1.5배)
MINIMUM_EMPLOYMENT_TENURE = 10               # 신규 (고용 후 10틱간 해고 금지)
```

---

## ✅ Part B: Starvation Fear Logic (가계 AI)
**File**: `simulation/decisions/ai_driven_household_engine.py`
**Target Method**: `make_decisions` (Labor Logic 섹션)

### B.1 Panic Labor (생존 본능)
**조건**: `Survival Need > SURVIVAL_PANIC_THRESHOLD` (80) 또는 `Food Inventory < FOOD_SECURITY_DAYS * Daily Consumption`
**행동**: `Reservation Wage` 계산을 무시하고 **최저임금 이하**라도 노동 공급.

```python
# [PSEUDO-CODE for Labor Decision]

# Scenario B: Unemployed
if not household.is_employed:
    agg_work = action_vector.work_aggressiveness
    
    # [PANIC CHECK] 식량 부족 또는 생존 위기
    food_inv = household.inventory.get("basic_food", 0.0)
    daily_need = getattr(config, "FOOD_CONSUMPTION_QUANTITY", 1.0)
    is_starving = household.needs.get("survival", 0) > config.SURVIVAL_PANIC_THRESHOLD
    is_food_insecure = food_inv < (daily_need * config.FOOD_SECURITY_DAYS)
    
    if is_starving or is_food_insecure:
        # PANIC MODE: 자존심 버리고 아무 일이나!
        reservation_wage = 0.01  # 사실상 무료 노동 (최소한의 값)
    else:
        # Normal Mode: 유보 임금 계산
        reservation_modifier = config.RESERVATION_WAGE_BASE - (agg_work * config.RESERVATION_WAGE_RANGE)
        reservation_wage = max(config.LABOR_MARKET_MIN_WAGE, market_avg_wage * reservation_modifier)
    
    orders.append(Order(household.id, "SELL", "labor", 1, reservation_wage, "labor"))
```

---

## ✅ Part C: Desperate Hiring Logic (기업 AI)
**File**: `simulation/decisions/ai_driven_firm_engine.py` (또는 Firm 의사결정 담당 파일)
**Target Method**: 임금 결정 로직

### C.1 Desperate Hiring (구인난 대응)
**조건**: `len(employees) == 0` AND `inventory < target`
**행동**: 임금을 `DESPERATE_HIRING_WAGE_MULTIPLIER` (1.5배)로 즉시 인상.
**제약**: 현금 보유량의 50%를 초과하는 임금 제안 금지 (파산 방지).

```python
# [PSEUDO-CODE for Wage Decision]

def determine_offered_wage(self, firm, config):
    base_wage = config.BASE_WAGE
    
    # [DESPERATE CHECK]
    if len(firm.employees) == 0 and sum(firm.inventory.values()) < firm.target_inventory:
        desperate_wage = base_wage * config.DESPERATE_HIRING_WAGE_MULTIPLIER
        
        # [DAMPING] 지불 능력 확인
        max_affordable = firm.cash / (config.MINIMUM_EMPLOYMENT_TENURE * 2)  # 20틱 버틸 수 있는 임금
        offered_wage = min(desperate_wage, max_affordable)
    else:
        # Normal wage adjustment logic
        offered_wage = base_wage * adjustment_factor
    
    return offered_wage
```

### C.2 Employment Tenure (고용 유지 의무)
**조건**: `ticks_since_hired < MINIMUM_EMPLOYMENT_TENURE` (10틱)
**행동**: 해고(Fire) 금지.

```python
# [PSEUDO-CODE for Fire Decision]

def consider_firing(self, employee, firm, config):
    if employee.ticks_since_hired < config.MINIMUM_EMPLOYMENT_TENURE:
        return False  # 해고 불가 (Tenure 보장)
    # ... 기존 해고 로직 ...
```

---

## ✅ Part D: Government Fiscal Rules (기존 유지)
**File**: `simulation/agents/government.py`

1. `calculate_approval_rating()`: 4대 지표 기반 지지율.
2. `adjust_fiscal_policy()`: 잉여금 30% 배당, 지지율 기반 세율 조정.
*(이미 구현되었다면 유지, 아니면 이전 지침 참조)*

---

## 🧪 Verification Criteria
1. **Iron Test (1000 ticks)** 실행.
2. **생존율**: `active_households >= 10` (50% 이상 생존)
3. **노동 시장**: 중간에 `L > 0`인 틱이 절반 이상.
4. **재정 안정**: 정부 현금이 발산하지 않음.
5. **로그 확인**: `PANIC_LABOR`, `DESPERATE_HIRING` 관련 로그 확인.

---

## ⚠️ Long-Term TODO (Deferred)
> **현재 접근법**: "배고프면 일해라" 하드코딩 (임시 미봉책)
> **이상적 접근법**: AI가 Reward Shaping을 통해 스스로 [생존 → 노동]을 학습
> *시뮬레이션 안정화 이후 별도 Phase에서 해결 예정*
