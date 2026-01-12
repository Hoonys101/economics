# 리펙토링 제안서: 관심사 분리 (SoC) 및 God Class 해소

**날짜:** 2026-01-12
**작성자:** Jules (AI Software Engineer)
**대상:** Simulation Core (`simulation/engine.py`, `simulation/core_agents.py`, `simulation/agents/government.py`)

## 1. 개요 (Executive Summary)

현재 시뮬레이션 코드베이스를 분석한 결과, 핵심 클래스들에서 **단일 책임 원칙 (SRP)** 및 **관심사 분리 (SoC)** 원칙을 위배하는 "God Class" 패턴이 식별되었습니다. 이러한 클래스들은 과도한 책임과 복잡성을 가지고 있어 유지보수성, 테스트 용이성, 그리고 확장성을 저해하고 있습니다.

본 리포트는 가장 시급한 리펙토링이 필요한 3가지 핵심 클래스(`Simulation`, `Household`, `Government`)를 선정하고, 구체적인 분리 및 리펙토링 방안을 제안합니다.

---

## 2. 식별된 God Classes 및 문제점 분석

### 2.1. `Simulation` Class (`simulation/engine.py`)
*   **현재 상태:** 53KB, 약 600+ 라인 (추정). 시뮬레이션의 "모든 것"을 알고 관리하는 전지전능한 객체입니다.
*   **주요 위반 사항:**
    *   **Lifecycle Management Mixing:** 에이전트의 생성, 초기화뿐만 아니라 파산(Liquidation), 사망, 상속 처리를 직접 수행하는 거대한 메서드(`_handle_agent_lifecycle`)를 포함하고 있습니다.
    *   **Logic Leakage:** `_update_social_ranks`, `_calculate_reference_standard` 와 같은 구체적인 사회학적 계산 로직이 엔진 레벨에 하드코딩되어 있습니다.
    *   **Consumption Logic inside Loop:** `run_tick` 메서드 내부에 "Vectorized Consumption Logic"이 절차적 코드로 길게 작성되어 있어, 틱 실행 흐름을 파악하기 어렵습니다.
    *   **Market Orchestration:** 개별 시장의 매칭과 정산을 직접 순회하며 처리하고 있습니다.

### 2.2. `Household` Class (`simulation/core_agents.py`)
*   **현재 상태:** 48KB. 경제적 주체, 생물학적 주체, 사회적 주체의 역할이 혼재되어 있습니다.
*   **주요 위반 사항:**
    *   **Mixed Domains:** `update_political_opinion` (정치), `decide_housing` (부동산 전략), `decide_and_consume` (경제 소비), `apply_leisure_effect` (시간 관리) 등 서로 다른 도메인의 로직이 하나의 클래스에 메서드로 나열되어 있습니다.
    *   **State Bloat:** `needs` (욕구), `inventory` (재고), `skills` (노동), `political_opinion` (정치), `social_rank` (사회) 등 성격이 다른 상태값들이 플랫하게 관리되고 있습니다.
    *   **System 2 Leakage:** 장기 계획(Housing Decision) 로직이 에이전트 클래스 메서드(`decide_housing`)로 직접 구현되어 있습니다.

### 2.3. `Government` Class (`simulation/agents/government.py`)
*   **현재 상태:** 25KB. 정책 수립(Brain)과 행정 집행(Body)이 혼재되어 있습니다.
*   **주요 위반 사항:**
    *   **Domain Coupling:** `run_public_education` (교육부), `run_welfare_check` (복지부), `invest_infrastructure` (국토부) 등 서로 다른 부처의 업무가 하나의 클래스에 메서드로 존재합니다.
    *   **Political Coupling:** 선거(`check_election`)와 지지율 관리 로직이 행정 집행 로직과 섞여 있습니다.

---

## 3. 리펙토링 제안 (Proposed Refactoring)

### 3.1. `Simulation` Class 분리 전략
`Simulation` 클래스는 오직 "조율자(Coordinator)" 역할만 수행해야 합니다.

1.  **`AgentLifecycleManager` 추출:**
    *   `_handle_agent_lifecycle` 메서드의 로직(파산 처리, 사망 처리, 상속)을 별도 클래스로 분리합니다.
    *   `Simulation`은 `lifecycle_manager.process_tick(agents)` 만 호출합니다.
2.  **`SocialStratificationSystem` 추출:**
    *   `_update_social_ranks`, `_calculate_reference_standard` 로직을 분리합니다.
    *   사회적 계층 계산을 전담하는 시스템 객체를 만듭니다.
3.  **`ConsumptionSystem` 추출:**
    *   `run_tick` 내의 Vectorized Consumption Logic을 별도 시스템으로 캡슐화합니다.
    *   `simulation.systems.consumption_system.py` 생성 제안.

### 3.2. `Household` Class 컴포넌트화 전략
`Household`는 상태 컨테이너로 남고, 로직은 컴포넌트로 위임합니다. (이미 일부 진행되었으나 가속화 필요)

1.  **`PoliticalComponent` 도입:**
    *   `update_political_opinion`, `approval_rating`, `discontent` 속성을 별도 컴포넌트로 분리합니다.
2.  **`HousingStrategy` 분리:**
    *   `decide_housing` 메서드와 관련 상태(`housing_target_mode`, `housing_price_history`)를 `System2Planner` 내부 혹은 별도 `HousingModule`로 완전히 이동시킵니다.
3.  **`DemographicState` 분리:**
    *   `age`, `gender`, `children_ids`, `death_prob` 등 인구통계학적 속성을 `Demographics` 객체로 묶어서 관리합니다.

### 3.3. `Government` Class 부처별 분리 전략
정부 기능을 '부처(Ministry)' 단위로 모듈화합니다.

1.  **`MinistryOfEducation` (교육부):**
    *   `run_public_education` 메서드와 교육 예산 관련 로직을 분리합니다.
2.  **`MinistryOfWelfare` (보건복지부):**
    *   `run_welfare_check`, `provide_subsidy` 로직을 분리합니다.
3.  **`PoliticalSystem` (정치 시스템):**
    *   `check_election`, `update_public_opinion`, `ruling_party` 상태를 관리하는 별도 시스템을 만듭니다.
    *   Government 에이전트는 현재 집권당의 정책 파라미터만 참조합니다.

---

## 4. 기대 효과 (Expected Benefits)

1.  **테스트 용이성 (Testability):**
    *   거대한 `Simulation` 객체를 생성하지 않고도, `EducationSystem`이나 `LifecycleManager`만 따로 단위 테스트가 가능해집니다.
2.  **유지보수성 (Maintainability):**
    *   특정 도메인(예: 교육 정책 변경) 수정 시, `Government` 클래스 전체가 아닌 `MinistryOfEducation`만 수정하면 되므로 사이드 이펙트가 최소화됩니다.
3.  **확장성 (Extensibility):**
    *   새로운 정부 기능(예: 국방, 환경) 추가 시 기존 클래스를 비대하게 만들지 않고 새로운 모듈을 플러그인 형태로 추가할 수 있습니다.

## 5. 결론 및 우선순위

가장 먼저 **`Simulation` 클래스의 `_handle_agent_lifecycle` 분리**와 **`Government` 클래스의 `run_public_education` 분리**를 우선적으로 진행할 것을 권장합니다. 이는 의존성이 비교적 명확하여 리펙토링 위험도가 낮으면서도 코드 가독성을 즉각적으로 개선할 수 있는 영역입니다.
