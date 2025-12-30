# Action Plan: Phase 1 - AI Integration & Refinement

## 1. Phase Goal

현재 AI의 역할을 '무엇을 할지(What)' 결정하는 고수준의 **전술(Tactic) 선택**에서, '어떻게 할지(How)'를 결정하는 **세부 파라미터(가격, 수량 등) 결정**까지 확장한다. 이를 통해 규칙 기반 로직에 대한 의존성을 줄이고, 에이전트가 환경과 상호작용하며 스스로 최적의 행동을 찾아가는 진정한 AI 기반 의사결정 모델로 발전시킨다.

---

## 2. Guiding Principles (기본 방침)

1.  **점진적 통합 (Incremental Integration):** 한 번에 모든 것을 AI로 전환하지 않는다. 가장 영향력이 큰 의사결정 변수(예: 기업의 판매 가격) 하나부터 시작하여 점진적으로 AI의 제어 범위를 넓힌다.

2.  **규칙 기반 엔진과 병행 (Keep Rule-Based Fallback):** 기존에 구현된 `RuleBased` 엔진은 AI 모델의 성능을 비교하고 검증하기 위한 **베이스라인(Baseline)**으로 계속 유지하고 활용한다.

3.  **데이터 기반 검증 (Data-Driven Verification):** 모든 AI 모델의 성능 향상은 `simulation_data.db`에 기록된 데이터를 기반으로 객관적으로 검증한다. (예: AI 기반 기업이 규칙 기반 기업보다 장기적으로 높은 수익을 내는가?)

4.  **테스트 주도 개발 (Test-Driven Development):** 새로 구현되는 모든 AI 의사결정 로직은 반드시 `pytest`를 이용한 단위/통합 테스트와 함께 개발되어야 한다.

---

## 3. Concrete Tasks (세부 실행 계획)

### Task 1: `AIDriven` 엔진 클래스 골격 생성

-   [x] **1.1.** `simulation/decisions/ai_driven_firm_engine.py` 파일 생성
    -   `BaseDecisionEngine`을 상속받는 `AIDrivenFirmDecisionEngine` 클래스 정의
    -   초기에는 `RuleBasedFirmDecisionEngine`을 내부적으로 호출하여, 전체적인 구조가 올바르게 동작하는지부터 확인.
-   [x] **1.2.** `simulation/decisions/ai_driven_household_engine.py` 파일 생성
    -   `BaseDecisionEngine`을 상속받는 `AIDrivenHouseholdDecisionEngine` 클래스 정의
    -   `RuleBasedHouseholdDecisionEngine`을 호출하는 초기 구현으로 시작.

### Task 2: 기업(Firm) AI 고도화 - AI의 가격 결정

-   [x] **2.1.** `AIDrivenFirmDecisionEngine` 수정
    -   `make_decisions` 메서드 내부에서, `ADJUST_PRICE` 전술이 선택되었을 때 `_adjust_price` 규칙을 호출하는 대신, AI가 직접 가격 결정을 하도록 로직 변경.
-   [x] **2.2.** `FirmAI` 액션(Action) 공간 재정의
    -   기존의 `Tactic` Enum을 반환하는 대신, 구체적인 가격 조정 행위(예: `(price, -0.1)`, `(price, 0)`, `(price, +0.1)`)를 액션으로 정의.
-   [x] **2.3.** `FirmAI` 보상(Reward) 함수 구체화
    -   가격 결정의 결과로 발생한 `수익(profit)` 또는 `매출(revenue)` 변화를 보상으로 명확하게 정의.
-   [x] **2.4.** 관련 테스트 코드 작성
    -   AI가 결정한 가격으로 판매 주문이 생성되는지 검증하는 `pytest` 테스트 작성.

### Task 3: 가계(Household) AI 고도화 - AI의 소비 선택

-   [x] **3.1.** `AIDrivenHouseholdDecisionEngine` 수정
    -   `EVALUATE_CONSUMPTION_OPTIONS` 전술이 선택되었을 때, '가성비(utility per dollar)' 규칙에 기반한 `_find_optimal_consumption_bundle`을 호출하는 대신, AI가 직접 구매할 재화를 선택하도록 로직 변경.
-   [x] **3.2.** `HouseholdAI` 액션(Action) 공간 재정의
    -   AI의 액션을 구매 가능한 재화 목록(예: `BUY_BASIC_FOOD`, `BUY_LUXURY_FOOD`, `DO_NOTHING`)으로 정의.
-   [x] **3.3.** `HouseholdAI` 보상(Reward) 함수 구체화
    -   재화 소비의 결과로 발생한 '욕구(Need) 감소량'을 보상으로 명확하게 정의.
-   [ ] **3.4.** 관련 테스트 코드 작성
    -   AI의 선택에 따라 특정 재화에 대한 구매 주문이 생성되는지 검증하는 `pytest` 테스트 작성.

### Task 4: 시뮬레이션 설정 업데이트

-   [ ] **4.1.** `config.py` 파일 수정
    -   시뮬레이션 시작 시 에이전트들에게 어떤 종류의 의사결정 엔진을 주입할지 선택할 수 있는 설정값(예: `DEFAULT_ENGINE_TYPE = "RuleBased"` 또는 `"AIDriven"`)을 추가.
-   [ ] **4.2.** `app.py` 파일 수정
    -   `create_simulation` 함수에서 `config.py`의 설정값을 읽어, 그에 맞는 엔진(`RuleBased...` 또는 `AIDriven...`)을 에이전트 생성 시 주입하도록 로직 수정.

### Task 5: 성능 분석 스크립트 작성

-   [ ] **5.1.** `analysis/` 디렉토리 생성
-   [ ] **5.2.** `compare_engine_performance.py` 스크립트 작성
    -   `simulation_data.db` 파일을 읽어, `RuleBased` 엔진을 사용한 시뮬레이션 런과 `AIDriven` 엔진을 사용한 시뮬레이션 런의 주요 지표(예: 기업 평균 자산, 가계 평균 욕구 충족도)를 비교하고 시각화하는 기능 구현.
