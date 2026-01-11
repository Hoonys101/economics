# Work Order: WO-048-Adaptive-Breeding

**Date:** 2026-01-11
**Phase:** Phase 22 (The Awakening) - Step 4
**Status:** Queued (After WO-050)
**Assignee:** Jules (Worker AI)
**Objective:** 가계(Household)가 경제적 효용/비용 분석(NPV)에 기반하여 출산 여부를 결정하도록 System 2 로직을 구현한다.

## 1. System Architecture (Hybrid Model)

피임 기술 보급 여부에 따라 의사결정 방식이 달라진다.

### Precondition: Technology Check
*   **Config Variable:** `TECH_CONTRACEPTION_ENABLED` (default: `True`)
*   **Logic:**
    *   `False` (Pre-Modern): System 1 작동 (확률 기반, 고출산).
    *   `True` (Modern): System 2 작동 (NPV 계산, 합리적 출산).

## 2. Decision Logic (Pseudo-code)

```python
def decide_reproduction(agent):
    if not is_fertile(agent):
        return False

    if not CONFIG.TECH_CONTRACEPTION_ENABLED:
        # Pre-Modern: Biological Imperative
        return random.random() < BIOLOGICAL_FERTILITY_RATE

    # Modern: System 2 Rational Calculation
    cost = calculate_total_cost(agent)
    benefit = calculate_total_benefit(agent)
    npv = benefit - cost

    return npv > 0
```

## 3. NPV Factors

### Cost (-)
*   **Raising Cost (C_raising):** `CHILD_MONTHLY_COST * 12 * 20` (월 양육비 × 20년).
*   **Opportunity Cost (C_opportunity):** `agent.wage * 0.5 * 20_years` (육아로 인한 소득 감소).
    *   **핵심 메커니즘:** 고소득자일수록 기회비용이 커져 출산을 기피함.

### Benefit (+)
*   **Emotional Utility (B_emotional):** 상수 또는 자산 대비 감소 함수.
*   **Old Age Support (B_support):** `Expected_Child_Income * 0.1` (자녀 용돈 기대).
    *   사회보장제도가 약할수록 이 값이 커짐 (후진국형 다산 재현).

## 4. Config Parameters

```python
TECH_CONTRACEPTION_ENABLED = True
BIOLOGICAL_FERTILITY_RATE = 0.15  # 피임 없을 때 월간 임신 확률
CHILD_MONTHLY_COST = 500.0
OPPORTUNITY_COST_FACTOR = 0.5  # 육아 시 소득 감소율
OLD_AGE_SUPPORT_RATE = 0.1
```

## 5. Verification Plan

1.  **Pre-Modern Test:** `TECH_CONTRACEPTION_ENABLED = False` → 고출산 확인.
2.  **Modern Test (High Income):** 고소득 가계 → 출산율 0.5명 미만 확인.
3.  **Modern Test (Low Income):** 저소득 가계 → 양육비 부담으로 출산 기피 확인.
4.  **Policy Test:** 정부 양육비 지원 → 출산율 반등 확인.
