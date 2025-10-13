### AI 기반 가계 소비 의사결정 강화 진행 보고 (2025년 9월 28일)

**1. 목표:**
`HouseholdDecisionEngine`을 개선하여 AI가 가계의 '인정(social)' 및 '성장(improvement)' 욕구에 대한 소비 결정을 내릴 수 있도록 강화합니다.

**2. 현재까지의 분석 결과:**

*   **`simulation/decisions/household_decision_engine.py` 분석:**
    *   `HouseholdDecisionEngine`은 `HouseholdAI`를 사용하여 `Tactic`을 결정하고, `_execute_tactic` 메서드를 통해 이를 시장 주문으로 변환합니다.
    *   현재 `_execute_tactic`은 `Tactic.BUY_ESSENTIAL_GOODS` 및 `Tactic.PARTICIPATE_LABOR_MARKET`만 처리합니다.
    *   `TODO` 주석에 `BUY_LUXURY_GOODS`, `INVEST_IN_STOCKS`, `TAKE_EDUCATION`에 대한 로직 추가가 명시되어 있습니다.

*   **`simulation/core_agents.py` 분석 (Household):**
    *   가계의 욕구는 `survival`, `asset`, `social`, `improvement`로 구성된 성격 기반 모델을 사용합니다.
    *   `social` 욕구는 '인정'에, `improvement` 욕구는 '성장'에 직접적으로 매핑됩니다.
    *   `consume` 메서드는 재화 소비 시 인벤토리 감소 및 욕구 충족 로직을 포함합니다. `goods_info_map`의 `utility_per_need`를 통해 재화가 어떤 욕구를 충족시키는지 정의됩니다.
    *   `calculate_social_status`는 자산과 사치품 소비를 기반으로 사회적 지위를 계산합니다.

*   **`simulation/ai/enums.py` 분석:**
    *   `Intention` Enum에 `SATISFY_SOCIAL_NEED` 및 `IMPROVE_SKILLS`가 이미 정의되어 있습니다.
    *   `Tactic` Enum에 `BUY_LUXURY_GOODS` (for `SATISFY_SOCIAL_NEED`) 및 `TAKE_EDUCATION` (for `IMPROVE_SKILLS`)이 이미 정의되어 있습니다.
    *   필요한 Enum 정의는 이미 완료되어 있습니다.

*   **`simulation/ai/household_ai.py` 분석:**
    *   `_get_strategic_state`는 `social` 및 `growth` 욕구를 이산화하여 상태에 포함합니다.
    *   `_get_tactical_state`는 `Intention.SATISFY_SOCIAL_NEED` (사치품 가격) 및 `Intention.IMPROVE_SKILLS` (교육 비용)에 대한 로직을 포함합니다.
    *   `_get_strategic_actions` 및 `_get_tactical_actions`는 이미 관련 `Intention` 및 `Tactic`을 포함합니다.
    *   `_calculate_reward`는 `social_need_reduction` 및 `growth_need_reduction`에 대한 보상을 계산합니다.
    *   **문제점:** `HouseholdAI` 생성자에서 `ai_decision_engine=None`으로 전달되는 순환 참조 문제가 존재하며, 이로 인해 `_calculate_reward`의 `predicted_reward` 통합이 현재 작동하지 않습니다.

**3. 다음 단계 계획:**

1.  **`ai_decision_engine` 순환 참조 문제 해결:**
    *   `simulation/ai_model.py` 파일을 분석하여 `AIDecisionEngine`의 역할과 구조를 이해합니다.
    *   `HouseholdAI`와 `AIDecisionEngine` 간의 순환 참조를 해결하고, `AIDecisionEngine` 인스턴스를 `HouseholdAI`에 올바르게 주입하는 방법을 모색합니다. (예: 초기화 후 주입)

2.  **"사치품" 및 "교육" 시장/재화 정의 및 접근 방식 확립:**
    *   `Tactic.BUY_LUXURY_GOODS`를 위해 `goods_data` 내에 "사치품"을 명확히 정의하고 (`is_luxury` 플래그 등), `HouseholdDecisionEngine`이 `goods_market`에서 해당 가격을 조회할 수 있도록 합니다.
    *   `Tactic.TAKE_EDUCATION`을 위해 "교육"이 시뮬레이션 내에서 어떻게 표현되고 획득되는지 (예: `goods_market`의 특정 재화, 별도의 교육 시장, 또는 직접적인 에이전트 행동) 정의합니다.

3.  **`HouseholdDecisionEngine`의 `_execute_tactic` 메서드 구현:**
    *   `Tactic.BUY_LUXURY_GOODS` 및 `Tactic.TAKE_EDUCATION`에 대한 구체적인 주문 생성 로직을 추가합니다.