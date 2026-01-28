# Work Order: WO-048-Adaptive-Breeding (Finalized Spec)

**Author:** Architect Prime
**Assignee:** Jules (Worker AI)
**Status:** Ready for Implementation (W-2)

## 1. Configuration (`config.py`)

기존 계획에 더해, NPV 계산의 균형을 맞추기 위한 **정서적 효용의 기준값(`CHILD_EMOTIONAL_VALUE_BASE`)**을 추가합니다. 이 값이 없으면 비용만 너무 커서 아무도 아이를 낳지 않는 '인류 멸망 시나리오'가 발생할 수 있습니다.

```python
# --- WO-048: Adaptive Breeding Parameters ---
TECH_CONTRACEPTION_ENABLED = True   # True: System 2 (NPV), False: System 1 (Random)
BIOLOGICAL_FERTILITY_RATE = 0.15    # 피임 없을 때의 월간 임신 확률

# Cost Factors
CHILD_MONTHLY_COST = 500.0          # 직접 양육비 (식비+교육비)
OPPORTUNITY_COST_FACTOR = 0.5       # 육아로 인한 임금 감소율 (50%)
RAISING_YEARS = 20                  # 양육 기간 (성인까지)

# Benefit Factors
CHILD_EMOTIONAL_VALUE_BASE = 200000.0 # 자녀 1명당 느끼는 정서적 가치의 총량 (화폐 환산)
OLD_AGE_SUPPORT_RATE = 0.1          # 자녀 소득의 10%를 노후 용돈으로 받음
SUPPORT_YEARS = 20                  # 은퇴 후 부양받는 기간
```

## 2. Logic Implementation (`household_ai.py`)

`HouseholdAI` 클래스 내 `decide_reproduction` 메서드를 아래 로직으로 재작성합니다.

### 🧠 Decision Algorithm

**Step 1: Technology Check**

* `if not config.TECH_CONTRACEPTION_ENABLED:`
    * **Action:** `return random.random() < config.BIOLOGICAL_FERTILITY_RATE`
    * (단, 에이전트 나이가 가임기인지 확인하는 기본 로직은 유지)

**Step 2: System 2 NPV Calculation (Modern Era)**

* **Cost Calculation (총비용):**
    1. **Direct Cost:** `C_direct = CHILD_MONTHLY_COST * 12 * RAISING_YEARS`
    2. **Opportunity Cost:** `C_opp = (agent.monthly_income * OPPORTUNITY_COST_FACTOR) * 12 * RAISING_YEARS`
        * *Note*: `agent.monthly_income` might need to be estimated from `current_wage * 20 days` (assuming 20 working days) or using `current_daily_income * 20`. Use `agent_data.get("current_wage", 0.0) * 8.0 * 20` as a standard monthly proxy if actual monthly income isn't tracked directly.
    3. `Total_Cost = C_direct + C_opp`

* **Benefit Calculation (총효용):**
    1. **Emotional Utility:** 한계효용 체감 법칙 적용.
        * `U_emotional = CHILD_EMOTIONAL_VALUE_BASE / (agent.children_count + 1)`
    2. **Old Age Support:** "내 자식은 나만큼은 번다"는 가정(Inherited Status) 적용.
        * `Expected_Child_Income = agent.monthly_income` (현재 부모 소득을 대리 변수로 사용)
        * `U_support = Expected_Child_Income * OLD_AGE_SUPPORT_RATE * 12 * SUPPORT_YEARS`
    3. `Total_Benefit = U_emotional + U_support`

* **Step 3: Final Decision**
    * `NPV = Total_Benefit - Total_Cost`
    * **Log Logic:** 디버깅을 위해 `NPV`, `Cost`, `Benefit` 값을 로그로 남길 것 (DEBUG Level).
    * **Result:** `return NPV > 0`

## 3. Verification Plan (`tests/test_wo048_breeding.py`)

다음 시나리오를 검증하는 독립형 테스트 스크립트를 작성하십시오.

### Scenario A: Pre-Modern Era
* **Set:** `TECH_CONTRACEPTION_ENABLED = False`
* **Expectation:** 소득과 무관하게 약 15% 확률로 `True` 반환.

### Scenario B: The Modernity Trap (High Income)
* **Set:** `TECH_CONTRACEPTION_ENABLED = True`
* **Agent:** 월 소득 10,000 (고소득)
* **Analysis:**
    * `C_opp`가 매우 높음 (10,000 * 0.5 * 12 * 20 = 1,200,000).
    * `U_support`도 높지만 (10,000 * 0.1 * 12 * 20 = 240,000), `C_opp`를 상쇄하기 힘듦.
* **Expectation:** `NPV < 0`  **출산 거부 (`False`)**

### Scenario C: The Poverty Trap (Low Income)
* **Agent:** 월 소득 1,000 (저소득)
* **Analysis:**
    * `C_direct` (500 * 12 * 20 = 120,000)가 소득 대비 비중이 너무 큼.
* **Expectation:** `NPV < 0`  **출산 거부 (`False`)**

### Scenario D: The Golden Mean (Middle Income) - *Calibration Target*
* **Agent:** 월 소득 3,000 ~ 5,000 (중산층)
* **Analysis:**
    * `U_emotional`이 비용을 상회하는 구간이 존재해야 함.
* **Expectation:** `NPV > 0`  **출산 (`True`)**
