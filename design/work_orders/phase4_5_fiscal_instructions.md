# W-2 Work Order: Operation "Responsible Ruler" (Phase 4.5)

> **Assignee**: Jules
> **Priority**: P0 (Emergency - Survival Critical)
> **Branch**: `feature/responsible-government`
> **Base**: `main`

---

## 📋 Overview
**목표**: 경제 시뮬레이션의 **가계 전멸(Total Extinction)** 문제를 해결하고, 정부를 지능형 에이전트로 업그레이드한다.

**핵심 과제**:
1.  **파라미터 튜닝**: 가계가 너무 빨리 죽지 않도록 초기 체력을 보강한다.
2.  **재정 준칙**: 정부가 돈을 쌓아두지 않고 국민에게 환급하게 만든다.
3.  **정치 반응**: 지지율에 따라 세율을 조절하게 만든다.

---

## ✅ Task 1: Survival Parameter Tuning (Config)
**File**: `config.py`

가계 수명을 늘리기 위해 아래 값들을 안전한 수준으로 상향 조정하십시오.

```python
# [SURVIVAL UPDATE]
INITIAL_HOUSEHOLD_ASSETS_MEAN = 20000.0  # (Was 5000.0) -> 충분한 초기 자금 제공
HOUSEHOLD_DEATH_TURNS_THRESHOLD = 10     # (Was 4) -> 굶어 죽기까지 유예 기간 연장
```

---

## ✅ Task 2: Implement Approval Logic
**File**: `simulation/agents/government.py` (or wherever `Government` class is defined)

`Government` 클래스에 지지율 계산 메서드를 추가하십시오.

```python
def calculate_approval_rating(self, households: List["Household"]) -> float:
    """
    모든 가계의 지지 여부를 종합하여 지지율(0.0 ~ 1.0)을 계산합니다.
    """
    approvals = 0
    total = 0
    
    for h in households:
        if not h.is_active: continue
        
        # 4대 지표 계산 (Spec 참조)
        # 1. Survival Score
        # 2. Relative Score
        # 3. Future Score
        # 4. Tax Score
        
        # 예시 구현:
        score = 0.0
        # ... (로직 구현) ...
        
        if score > 0:
            approvals += 1
        total += 1
        
    if total == 0: return 0.0
    self.approval_rating = approvals / total
    return self.approval_rating
```

---

## ✅ Task 3: Implement Fiscal Loop
**File**: `simulation/agents/government.py`

매 틱(또는 10틱마다) 실행될 재정 조정 로직을 구현하십시오.

```python
def adjust_fiscal_policy(self, households):
    # 1. 지지율 갱신
    self.calculate_approval_rating(households)
    
    # 2. 잉여금 분배 (Citizen Dividend)
    target_reserve = self.last_gdp * 0.10
    excess_cash = self.cash - target_reserve
    
    if excess_cash > 0 and self.inflation_rate < 0.05:
        payout = excess_cash * 0.3  # 30%만 분배
        per_capita = payout / len(households)
        for h in households:
            if h.is_active:
                h.assets += per_capita
        self.cash -= payout
        
    # 3. 세율 조정 (Political Response)
    current_tax = self.config.TAX_BRACKETS[-1][1] # 최고세율 기준
    
    if self.approval_rating < 0.40:
        # 위기: 감세
        new_tax = max(0.05, current_tax - 0.01)
        # Config 업데이트 로직 필요 (또는 동적 변수 사용)
        
    elif self.approval_rating > 0.60:
        # 여유: 증세
        new_tax = min(0.50, current_tax + 0.01)

---

## ✅ Task 4: Enhance Market Responsiveness (Crucial)
**시장 경직성 해결**: 아사(Death)보다 시장 반응이 느리면 전멸합니다. 아래 "위기 반응(Panic Logic)"을 반드시 추가하십시오.

1.  **Panic Labor (Household)**:
    - 조건: `Survival Need > 80` (굶어 죽기 직전)
    - 행동: `Reservation Wage` 하한선(`MIN_WAGE`)을 무시하고, **현재 시장 최저가보다 낮게**라도 노동 공급.
    - 구현: `AIDrivenHouseholdDecisionEngine`에서 `reservation_wage` 계산 시 Safe Guard 해제.

2.  **Desperate Hiring (Firm)**:
    - 조건: `Employees == 0` AND `Inventory < Target` (일손이 없어 망하기 직전)
    - 행동: 임금 인상폭 제한(`WAGE_INFLATION_ADJUSTMENT`)을 무시하고, **즉시 1.5배~2배** 임금 제시.
    - 구현: `AIDrivenFirmDecisionEngine`에서 임금 결정 로직에 예외 처리 추가.

---

## 🧪 Verification Criteria
1.  **Iron Test (1000 ticks)** 실행.
2.  **생존율**: `active_households >= 10` (50% 이상 생존)
3.  **재정 안정**: 정부 현금이 무한대로 발산하지 않고 일정 수준 유지.

4.  **로그 확인**: `FISCAL_POLICY | Tax Rate adjusted to...` 또는 `DIVIDEND | Distributed...` 로그 확인.
