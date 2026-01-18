# 관심사의 분리(SoC) 기반 리펙토링 제안서

**작성일:** 2026년 1월 17일
**작성자:** Jules (AI Software Engineer)
**대상:** 경제 시뮬레이션 엔진 (`simulation` 패키지)

---

## 1. 개요 (Overview)

현재 코드베이스에 대한 정적 분석 결과, 시스템의 복잡도가 증가함에 따라 몇몇 핵심 클래스들이 비대해지고 여러 책임을 동시에 수행하는 "God Class" 형태를 띠고 있습니다. 이는 유지보수성, 테스트 용이성, 그리고 기능 확장을 저해하는 요소입니다.

본 제안서는 **관심사의 분리(Separation of Concerns, SoC)** 원칙에 따라, 가장 리펙토링이 시급한 3가지 핵심 클래스(`Simulation`, `Household`, `Firm`)를 식별하고, 이를 컴포넌트 기반 아키텍처로 분리하는 구체적인 방안을 제시합니다.

---

## 2. God Class 분석 및 제안

### 2.1. Simulation Class (`simulation/engine.py`)

**현재 상태:**
- **코드 규모:** 약 885 Lines
- **역할:** 시뮬레이션 루프 실행, 시간 관리, 모든 에이전트(가계, 기업, 정부)의 수명주기 관리, 시장 청산 조정, 데이터 수집, 이벤트 주입 등 시스템의 모든 측면을 관장함.
- **문제점:**
    - `run_tick` 메서드가 너무 많은 도메인 로직(정부 정책 실행, 은행 이자 계산, 마켓 클리어링 등)을 직접 호출하며 제어함.
    - 데이터 수집(`tracker`)과 로직 실행이 혼재되어 있음.
    - 새로운 시스템(예: HousingSystem, SocialSystem) 추가 시 `Simulation` 클래스 수정이 불가피함 (OCP 위반).

**리펙토링 제안:**
`Simulation` 클래스를 순수한 **조정자(Coordinator)** 역할로 축소하고, 하위 책임을 전담 매니저에게 위임합니다.

*   **`SimulationRunner` (New):** 메인 루프(`run_tick`)와 시간 진행만을 담당하는 실행기.
*   **`WorldState` (New):** `households`, `firms`, `markets`, `agents` 등의 상태 데이터를 담는 컨테이너. 로직 없이 데이터만 보유.
*   **`SystemScheduler` (New):** 각 서브시스템(`BankSystem`, `GovernmentSystem`, `MarketSystem`)의 실행 순서를 관리하고 호출.
*   **`LifecycleManager` (Enhance):** 에이전트 생성, 사망, 상속, 창업 등 생명주기 관리 전담 (현재 일부 존재하나 역할 강화 필요).
*   **`MetricsCollector` (Refactor):** `EconomicIndicatorTracker` 등을 통합 관리하며, 시뮬레이션 로직과 분리된 관찰자(Observer) 패턴 적용.

---

### 2.2. Household Class (`simulation/core_agents.py`)

**현재 상태:**
- **코드 규모:** 약 700+ Lines (in `core_agents.py`)
- **역할:** 생물학적 욕구(식량, 생존), 경제적 활동(노동, 소비, 자산관리), 사회적 활동(정치, 지위), 의사결정(AI Wrapper)을 모두 포함.
- **문제점:**
    - `update_needs` 메서드 내에서 소비, 생존, 성격 변화 등이 뒤섞여 실행됨.
    - 인구통계학적 속성(`DemographicsComponent`)과 경제적 속성이 강하게 결합됨.
    - AI 모델 학습을 위한 데이터 스냅샷 로직이 비즈니스 로직과 혼재.

**리펙토링 제안:**
**컴포넌트 기반 설계(Composition over Inheritance)**를 강화하여 `Household`를 껍데기(Shell)로 만들고 기능을 컴포넌트로 위임합니다.

*   **`HouseholdBiology`:** 생존 욕구(Hunger), 나이, 건강, 사망 확률 계산.
*   **`HouseholdEconomy`:** 자산(Assets), 인벤토리(Inventory), 가계부(Income/Expense), 포트폴리오 관리.
*   **`HouseholdSocial`:** 사회적 지위(Status), 정치 성향(Political Opinion), 관계(Genealogy) 관리.
*   **`HouseholdLabor`:** 노동 스킬(Skill), 직업(Job), 임금 기대(Reservation Wage) 관리.
*   **`System2Planner` (Existing):** 장기 의사결정(주택 구매 등) 전담 (현재 존재하나 역할 명확화).

-> `Household` 클래스는 위 컴포넌트들을 소유하고, `DecisionEngine`의 판단을 각 컴포넌트에 전달하는 **메시지 패싱(Message Passing)** 역할만 수행해야 합니다.

---

### 2.3. Firm Class (`simulation/firms.py`)

**현재 상태:**
- **코드 규모:** 약 734 Lines
- **역할:** 생산, 고용/해고, 급여 지급, 마케팅, 재무 관리, 주식 발행(IPO), 기업 가치 평가.
- **문제점:**
    - 이미 `Department` 패턴(HR, Finance, Production, Sales)이 도입되었으나, 여전히 `Firm` 클래스 레벨에서 `distribute_profit`, `calculate_valuation`, `init_ipo` 등의 핵심 로직을 직접 수행함.
    - 재고 관리(Inventory) 로직이 분산되어 있음.

**리펙토링 제안:**
부서(Department) 패턴을 완성하고, `Firm`은 **전략적 의사결정의 주체**로만 남깁니다.

*   **`LogisticsDepartment` (New):** 원자재 및 완제품 재고 관리, 인벤토리 평가, 감가상각 처리 전담.
*   **`InvestorRelations` (New):** 주식 발행(IPO/SEO), 배당금 정책 실행, 주주 명부 관리, 기업 가치(Valuation) 계산 전담.
*   **`FirmSystem2Planner` (Enhance):** 사업 확장, M&A, R&D 투자 등 장기 전략 수립 전담.
*   **기존 부서 강화:**
    *   `FinanceDepartment`: 세금 납부 및 파산 처리 로직을 완전히 가져옴.
    *   `HRDepartment`: 임금 협상 및 노동 생산성 관리 로직 통합.

---

## 3. 기대 효과 (Expected Benefits)

1.  **테스트 용이성 (Testability):** 거대한 클래스를 통째로 모킹(Mocking)할 필요 없이, `FinanceDepartment`, `HouseholdBiology` 등 작은 단위 컴포넌트별로 유닛 테스트가 가능해집니다.
2.  **유지보수성 (Maintainability):** 특정 로직(예: 세금 계산 방식 변경) 수정 시, 해당 컴포넌트만 수정하면 되므로 사이드 이펙트(Side Effect)가 최소화됩니다.
3.  **확장성 (Extensibility):** 새로운 기능(예: 질병 시스템) 추가 시 `Household` 코드를 건드리지 않고 `DiseaseComponent`를 부착하는 방식으로 확장이 가능합니다.
4.  **가독성 (Readability):** 코드의 책임이 명확해져 개발자가 비즈니스 로직을 이해하는 속도가 빨라집니다.

## 4. 실행 계획 (Action Plan)

1.  **Phase 1 (준비):** 각 God Class에 대한 상세 의존성 그래프 작성 및 테스트 커버리지 확보.
2.  **Phase 2 (추출):**
    *   `Firm`: `LogisticsDepartment`, `InvestorRelations` 추출.
    *   `Household`: `HouseholdEconomy`, `HouseholdBiology` 분리.
    *   `Simulation`: `MetricsCollector`, `SystemScheduler` 분리.
3.  **Phase 3 (검증):** 리펙토링 전후의 시뮬레이션 결과(GDP, 인구수 등 매크로 지표)가 일치하는지 확인 (Regression Test).

위 제안에 대한 검토 및 승인을 요청드립니다.
