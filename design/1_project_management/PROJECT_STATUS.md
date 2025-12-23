# 프로젝트 상태 보고서 (PROJECT_STATUS.md)

이 문서는 "살아있는 디지털 경제" 프로젝트의 현재 진행 상황, 다음 단계, 그리고 주요 이슈를 종합적으로 관리하는 단일 문서입니다.

---

## 1. 현재 개발 단계 및 목표

- **현재 단계:** `Phase 1: AI 통합 및 고도화 (AI Integration & Refinement)`
- **현재 목표:** AI 에이전트가 단순한 규칙 기반 반응을 넘어, 학습을 통해 지능적으로 행동하도록 만드는 것을 목표로 합니다. 특히 가계(Household) 에이전트의 의사결정 로직을 기존의 규칙 기반 시스템에서 AI 기반 시스템(`AIDrivenHouseholdDecisionEngine`)으로 완전히 전환하는 데 집중합니다.

---

## 2. Phase 1 주요 완료 작업 (2025-11-04 기준)

*   **AI 모델 학습 및 평가 지표 고도화:**
    *   `reward_calculator.py`를 개선하여 장기적 목표(성장, 자산 축적 욕구)를 반영하는 보상 함수를 설계했습니다.
    *   `learning_tracker.py`를 구현하여 Q-테이블 변화량, 보상 등 학습 진행 상황을 추적하는 기능을 추가했습니다.
    *   학습 속도, 전략 다양성 등 AI 성능 분석을 위한 새로운 지표를 `design/ai_learning_metrics.md`에 정의했습니다.

*   **모방 학습 메커니즘 구현:**
    *   `AITrainingManager` 컴포넌트를 `simulation/ai/ai_training_manager.py`에 구현했습니다.
    *   `simulation/engine.py`에 `AITrainingManager`를 통합하고, 시뮬레이션 루프에서 주기적으로 호출하는 로직을 추가했습니다.

*   **AI 전술 실행 로직 구현 (기업 가격 결정):**
    *   `RuleBasedFirmDecisionEngine`의 가격 결정 로직을 `AIDrivenFirmDecisionEngine`으로 이전하여, AI가 전술 선택뿐만 아니라 실행까지 직접 담당하도록 아키텍처를 개선했습니다.

*   **DB 기반 리팩토링 및 테스트 오류 해결:**
    *   `DBManager`를 `SimulationRepository`로 대체하고, 관련 모듈의 의존성을 모두 수정했습니다.

*   **가계(Household) AI 고도화 - AI의 소비 선택 테스트:**
    *   AI가 생존 욕구가 높을 때 'food' 구매 주문을 생성하는지 검증하는 `pytest` 테스트(`test_ai_creates_purchase_order`)를 `tests/test_household_ai.py`에 추가하고, 관련 오류를 수정하여 테스트를 통과시켰습니다.

*   **가계 투기적/완충재 수요 도입:**
    *   `simulation/ai/enums.py`에 `BUY_FOR_BUFFER` 전술을 추가했습니다.
    *   `config.py`에 `TARGET_FOOD_BUFFER_QUANTITY` 및 `PERCEIVED_FAIR_PRICE_THRESHOLD_FACTOR`를 추가했습니다.
    *   `AIDrivenHouseholdDecisionEngine`에 `BUY_FOR_BUFFER` 전술 실행 로직을 구현했습니다.
    *   `HouseholdAI`의 전술적 상태에 이산화된 재고 및 가격 유리함 정보를 포함하고, 행동 공간 및 보상 함수에 `BUY_FOR_BUFFER`를 추가했습니다.

*   **가계(Household) 의사결정 AI 이전 완료:**
    *   `AIDrivenHouseholdDecisionEngine`을 구현하고 `Household` 클래스와 통합했습니다.
    *   `execute_tactic` 메서드를 통해 AI의 전략/전술(노동 공급, 상품 소비)이 실제 행동으로 이어지도록 구현했습니다.

*   **모방 및 진화 학습 메커니즘 구현 완료:**
    *   `AITrainingManager`를 통해 상위 10% 에이전트(Role Model)의 지식을 하위 50% 에이전트(Learner)에게 복제하는 모방 학습을 구현했습니다.
    *   전략(Intention)과 전술(Tactic) Q-테이블을 모두 복제하며, 무작위 변이(Mutation)를 적용하여 다양성을 확보했습니다.
    *   `Simulation` 엔진에 학습 주기를 연동하여 시뮬레이션 중 지속적인 학습이 일어나도록 했습니다.

*   **프론트엔드 인증 구현:**
    *   `templates/index.html`에 Secret Token 입력 필드를 추가하고, API 요청 시 인증 헤더를 포함하도록 수정하여 프론트엔드와 백엔드 간의 연동 문제를 해결했습니다.

*   **주요 오류 해결:**
    *   `AttributeError: module 'config' has no attribute 'FIRM_PRODUCTION_TARGETS'`
    *   `sqlite3.ProgrammingError: Cannot operate on a closed database.` (시뮬레이션 스레드 및 API 엔드포인트)
    *   `NameError: name 'HouseholdAI' is not defined`
    *   `AttributeError: 'AIDecisionEngine' object has no attribute '_get_strategic_state'`
    *   `AttributeError: 'FirmAI' object has no attribute '_discretize'`
    *   `NameError: name 'Aggressiveness' is not defined`
    *   `AttributeError: 'tuple' object has no attribute 'name'`
    *   `AttributeError: 'OrderBookMarket' object has no attribute 'place_place_order'`
    *   `TypeError: AIDrivenFirmDecisionEngine.make_decisions() missing 2 required positional arguments: 'market_data' and 'current_time'`
    *   `AttributeError: 'float' object has no attribute 'values'`

---

## 3. 다음 실행 계획 (Next Steps)

`design/project_management/action_plans/phase_1_ai_integration_plan.md` 체크리스트에 따라 `Phase 1`의 남은 과제를 진행합니다.

1.  **시뮬레이션 설정 업데이트:**
    *   `config.py` 파일에 `DEFAULT_ENGINE_TYPE` 설정값을 추가하여 시뮬레이션 시작 시 에이전트들에게 어떤 종류의 의사결정 엔진을 주입할지 선택할 수 있도록 합니다. (현재 `AIDriven`으로 고정)
    *   `app.py` 파일의 `create_simulation` 함수에서 `config.py`의 설정값을 읽어, 그에 맞는 엔진(`RuleBased...` 또는 `AIDriven...`)을 에이전트 생성 시 주입하도록 로직을 수정합니다. (현재 `RuleBased` 엔진이 존재하지 않아 `AIDriven`으로 고정)

2.  **성능 분석 스크립트 작성:**
    *   `analysis/` 디렉토리에 `compare_engine_performance.py` 스크립트를 작성하여 `RuleBased` 엔진과 `AIDriven` 엔진을 사용한 시뮬레이션 런의 주요 지표를 비교하고 시각화하는 기능을 구현합니다.

---

## 4. 현재 코드 상태 및 주요 이슈

*   **테스트:** 모든 단위 및 통합 테스트가 **성공(PASS)**하는 안정적인 상태입니다.
*   **아키텍처:** AI 중심의 의사결정 구조와 DB 기반 데이터 관리 구조가 성공적으로 적용되었습니다.
*   **블로커:** 현재 특별한 블로커는 없으며, 계획에 따라 다음 개발을 진행할 수 있습니다. 다만, `RuleBased` 엔진이 현재 코드베이스에 존재하지 않아 `config.DEFAULT_ENGINE_TYPE` 설정이 `AIDriven`으로 고정될 예정입니다. 향후 `RuleBased` 엔진을 복원하거나 재구현할 필요가 있을 수 있습니다.

---

## 5. 버전 관리 및 아카이빙 (Version Control & Archiving)

본 프로젝트의 V1 경제 시뮬레이션 모델의 최종 상태는 Git 로컬 저장소에 스냅샷으로 보관되었습니다. 이 버전은 비록 경제적 불안정성(임금 경직성, 가격 초인플레이션 등)을 보이지만, 코드 자체는 오류 없이 정상적으로 구동되며 시뮬레이션 틱을 완료하고 결과 파일을 생성합니다.

*   **브랜치명:** `feature/gemini/v1-economic-model-snapshot`
*   **목적:** 향후 V2 설계 구현과의 비교 및 레거시 코드 참조를 위한 기준점 역할을 합니다.
*   **상태:** 로컬 저장소에만 커밋되어 있으며, 원격 저장소에는 푸시되지 않았습니다. 이는 사용자의 지시에 따라 로컬 아카이빙 목적으로만 유지됩니다.