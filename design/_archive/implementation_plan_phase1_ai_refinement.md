# 실행 계획: Phase 1 - AI 통합 및 고도화

이 문서는 'Phase 1: AI 통합 및 고도화'의 두 번째 단계인 '가계 AI 이전' 및 '모방 학습 구현'을 위한 구체적인 개발 작업 체크리스트입니다.

## 1. 가계(Household) 의사결정 AI 이전

-   [ ] **`AIDrivenHouseholdDecisionEngine` 클래스 구현:**
    -   [ ] `ai_model.py`에 `AIDrivenHouseholdDecisionEngine` 클래스 생성.
    -   [ ] 계층적 Q-러닝 로직에 따라 `get_decision()` 메서드 구현 (상태인식 -> Intention 선택 -> Tactic 선택).

-   [X] **`Household` 클래스에 전술 실행기(`execute_tactic`) 구현:**
    -   [X] `agents/household.py`의 `Household` 클래스에 `execute_tactic(self, tactic, aggressiveness)` 메서드 추가.
    -   [ ] **노동 공급 전술 실행:**
        -   [ ] `tactic`이 `PARTICIPATE_LABOR_MARKET`일 경우, `aggressiveness` 값에 따라 `reservation_wage`를 동적으로 설정하는 로직 구현.
    -   [ ] **상품 소비 전술 실행:**
        -   [ ] `tactic`이 `BUY_GOODS` 계열일 경우, AI가 결정한 `consumption_ratio`로 예산을 계산하는 로직 구현.
        -   [ ] `aggressiveness` 값에 따라 시장 가격 대비 지불 용의(Willingness to Pay)를 조절하는 로직 구현.

-   [ ] **시뮬레이션 엔진 연동:**
    -   [ ] `simulation/engine.py`의 `run_tick` 메서드 수정.
    -   [ ] 기존의 규칙 기반 가계 의사결정 로직을 `AIDrivenHouseholdDecisionEngine.get_decision()` 및 `Household.execute_tactic()` 호출로 대체.

-   [ ] **테스트 코드 작성 및 검증:**
    -   [ ] `AIDrivenHouseholdDecisionEngine`의 의사결정 과정을 검증하는 단위 테스트 작성.
    -   [ ] `Household.execute_tactic`이 `aggressiveness`에 따라 다르게 작동하는지 검증하는 단위 테스트 작성.
    -   [ ] 전체 시뮬레이션이 가계 AI를 통해 정상적으로 작동하는지 통합 테스트 실행 및 확인.

## 2. 모방 및 진화 학습 메커니즘 구현

-   [X] **`AITrainingManager` 클래스 구현:**
    -   [X] `simulation/ai/ai_training_manager.py` 파일 생성 및 `AITrainingManager` 클래스 정의.

-   [X] **주기적 모방 학습 기능 구현:**
    -   [X] `run_imitation_learning_cycle()` 메서드 구현.
    -   [X] 자산 기준 상위 10% 에이전트와 하위 50% 에이전트를 식별하는 로직 추가.
    -   [X] 상위 에이전트의 전략 Q-테이블(`Q_strategy`)을 하위 에이전트에게 복제하는 로직 구현.
    -   [X] `simulation/engine.py`의 `run_tick`에서 특정 주기(예: 1000틱)마다 위 메서드를 호출하도록 연동.

-   [X] **신규 에이전트 생성 시 복제 기능 구현:**
    -   [X] `clone_from_fittest_agent()` 메서드 구현.
    -   [X] 현재 가장 자산이 많은 에이전트의 Q-테이블(전략+전술)을 복제하는 로직 추가.
    -   [ ] 에이전트 생성 로직(`create_new_household`)에서 위 메서드를 호출하도록 수정. (Note: Dynamic agent creation not yet implemented in Engine)

-   [X] **변이(Mutation) 기능 구현:**
    -   [X] Q-테이블을 복제할 때, 값에 작은 무작위 노이즈를 추가하는 `_apply_mutation()` 내부 메서드 구현.

-   [X] **테스트 코드 작성 및 검증:**
    -   [X] `AITrainingManager`의 각 기능(상위/하위 에이전트 식별, Q-테이블 복제, 변이 적용)에 대한 단위 테스트 작성.

## 3. 최종 정리 및 문서화

-   [ ] **모든 테스트 통과 확인:** 프로젝트의 모든 테스트(단위, 통합)를 실행하여 100% 통과 확인.
-   [ ] **`PROJECT_STATUS.md` 업데이트:** 위 작업들의 완료 상태를 반영하여 문서 최신화.
