# 설계안: 다중 재화 및 효용 기반 경제 모델

이 문서는 다중 재화 경제 모델 도입을 위한 구체적인 기술 설계와 구현 체크리스트를 정의합니다.

## Phase 1: 기반 시스템 구축 (Foundation)

-   [x] **`config.py` 설정 재정의**
    -   [x] `GOODS` 설정을 단순 리스트에서 각 재화의 특성을 담은 딕셔너리 객체로 변경합니다.
    -   [x] 각 재화 객체에 다음 속성을 포함합니다:
        -   `production_cost`: 생산 비용
        -   `utility_effects`: 이 재화가 어떤 욕구(`survival`, `social` 등)를 얼마나 충족시키는지 정의하는 딕셔너리 (예: `{'survival': 10, 'social': 5}`)
    -   [x] `FIRM_SPECIALIZATIONS` 설정을 추가하여, 시뮬레이션 시작 시 기업들이 어떤 재화를 전문적으로 생산할지 지정합니다.

-   [x] **시장(`Market`) 시스템 확장**
    -   [x] `simulation/engine.py`의 `Simulation` 클래스 초기화 시, `config.GOODS` 설정을 순회합니다.
    -   [x] 각 재화의 이름(`good_name`)을 키로, `OrderBookMarket(good_name)` 인스턴스를 값으로 하는 딕셔너리(`self.markets`)를 생성하여, 재화별 독립적인 시장을 관리합니다.

-   [x] **기업(`Firm`) 에이전트 수정**
    -   [x] `simulation/agents/firm.py`의 `Firm` 클래스 생성자에 `specialization` 인자를 추가하여 생산 전문 분야를 명시적으로 할당합니다.
    -   [x] `produce` 메서드가 자신의 `specialization`에 해당하는 재화만 생산하도록 로직을 수정합니다.

## Phase 2: AI 및 의사결정 로직 수정 (Intelligence)

-   [x] **가계(`HouseholdDecisionEngine`) 로직 전면 개편**
    -   [x] `simulation/decisions/household_decision_engine.py`의 `make_decisions` 메서드 로직을 재설계합니다.
    -   [x] `_get_consumption_candidates` 신규 메서드: 시장에서 구매 가능한 모든 소비재(기본/고급 식량) 목록과 가격 정보를 가져옵니다.
    -   [x] `_calculate_utility_gain` 신규 메서드: 특정 재화를 소비했을 때 얻게 될 총 효용 증가량을 가계의 현재 욕구 상태와 재화의 `utility_effects`를 기반으로 계산합니다.
    -   [x] `_find_optimal_consumption_bundle` 신규 메서드: 주어진 예산 제약 하에서 '비용 대비 효용'을 기준으로 최적의 구매 조합(어떤 물건을 몇 개 살지)을 결정하는 핵심 로직을 구현합니다.
    -   [x] `make_decisions`의 반환값: 결정된 구매 조합에 따라 여러 개의 `place_order` 액션을 생성하도록 수정합니다.

-   [x] **AI 엔진(`HouseholdAI`) 재설계**
    -   [x] `simulation/ai/household_ai.py`의 `_get_tactical_state` 메서드가 `basic_food_price`, `luxury_food_price` 등 경쟁 재화들의 시장 정보를 상태에 포함하도록 수정합니다.
    -   [x] `Tactic` Enum의 `BUY_FOOD`를 `EVALUATE_CONSUMPTION_OPTIONS`으로 변경합니다. 이는 AI가 직접 구매를 명령하는 대신, '최적 소비 조합 탐색' 단계를 촉발하도록 역할을 변경하는 것입니다.
    -   [x] `_calculate_reward` 메서드가 지출한 비용과 그로 인해 얻은 '총 효용'을 함께 고려하여 보상을 계산하도록 수정합니다.

## Phase 3: 검증 및 시스템 통합 (Verification & Integration)

-   [x] **신규 테스트 케이스 작성**
    -   [x] `tests/` 디렉토리에 `test_household_decision_engine_multi_good.py` 테스트 파일을 신규 생성합니다.
    -   [x] '고급 식량'이 '기본 식량'보다 비쌀 때, 가계가 '기본 식량'을 우선 구매하는지 검증하는 테스트 케이스를 추가합니다.
    -   [x] 예산이 충분할 때, 가계가 두 재화를 섞어서 구매하는지 검증하는 테스트 케이스를 추가합니다.

-   [x] **시뮬레이션 엔진(`Simulation Engine`) 통합**
    -   [x] `simulation/engine.py`의 `run_tick` 메서드가 가계로부터 전달받은 다중 구매 주문(여러 `place_order` 액션)을 올바르게 처리하여, 각 재화에 맞는 시장(`self.markets[good_name]`)에 정확히 전달하는지 확인하고 수정합니다.