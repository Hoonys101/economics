# 리펙토링 제안서: 관심사의 분리(SoC) 및 God Class 해소

**작성일:** 2026-01-16
**작성자:** Jules (AI Software Engineer)
**대상:** Simulation Core Team

---

## 1. 개요 (Executive Summary)

현재 시뮬레이션 코드베이스에 대한 분석 결과, 주요 클래스들이 과도한 책임을 지고 있는 **God Class** 형태를 띠고 있음이 확인되었습니다. 이는 **관심사의 분리(SoC, Separation of Concerns)** 원칙을 위배하며, 유지보수성, 테스트 용이성, 그리고 확장성을 저해하는 주요 요인입니다.

본 제안서는 코드베이스 내 가장 비대한 3개의 클래스(`Simulation`, `Household`, `Firm`)를 식별하고, 이를 더 작고 응집도 높은 컴포넌트로 분리하기 위한 리펙토링 전략을 제시합니다.

---

## 2. 식별된 God Class 및 문제점 분석

### 2.1. Simulation Class (`simulation/engine.py`)
*   **현재 규모:** 약 1,042 Lines of Code (LOC)
*   **주요 책임 (현재 혼재됨):**
    *   **Agent Orchestration:** 에이전트 생성, 틱(Tick) 진행, 루프 관리.
    *   **Market Logic:** 시장 데이터 집계(`_prepare_market_data`), 화폐 공급량 계산(`_calculate_total_money`), 주식 거래 처리.
    *   **Event Handling:** 카오스 이벤트(인플레이션, 경기 침체 등) 하드코딩.
    *   **Data Logging:** 버퍼 관리(SMA 계산), 통계 추적.
    *   **AI Training Loop:** 학습 데이터 수집 및 보상 계산 로직.
*   **문제점:**
    *   `run_tick` 메서드가 약 300줄에 달하며, 절차지향적인 로직이 과도하게 집중됨.
    *   시장 메커니즘 변경 시 엔진 코드를 수정해야 함 (OCP 위배).
    *   테스트를 위해 전체 엔진을 Mocking 해야 하는 어려움.

### 2.2. Household Class (`simulation/core_agents.py`)
*   **현재 규모:** 약 1,079 Lines of Code (LOC)
*   **주요 책임 (현재 혼재됨):**
    *   **Bio-Logic:** 나이, 성별, 욕구(Needs), 생존 로직.
    *   **Economic Logic:** 소비, 노동, 세금, 자산 관리, 포트폴리오.
    *   **Psychology:** 성격, 행복도, 인플레이션 기대심리, 정치적 성향.
    *   **Social Logic:** 사회적 지위, 주거 결정(System 2).
    *   **Legacy/Shadow Logic:** 섀도우 임금 계산, 시장 기록 관리.
*   **문제점:**
    *   `Household` 객체 하나가 인간의 생물학적 특성부터 복잡한 경제적 의사결정까지 모두 포함.
    *   일부 컴포넌트화(`DemographicsComponent`)가 진행되었으나, 여전히 메인 클래스가 Facade 이상의 로직을 직접 수행함.
    *   `make_decision` 메서드 내에 주택 구매 로직 등이 하드코딩되어 있음.

### 2.3. Firm Class (`simulation/firms.py`)
*   **현재 규모:** 약 716 Lines of Code (LOC)
*   **주요 책임 (현재 혼재됨):**
    *   **Business Operations:** 생산, 재고 관리.
    *   **Financials:** IPO, 유상증자, 배당, 밸류에이션(Valuation).
    *   **Market Strategy:** 섀도우 가격(Shadow Price) 계산, 마케팅 예산 책정.
    *   **Facade Boilerplate:** 하위 부서(`HR`, `Finance` 등)로의 단순 위임 프로퍼티가 클래스 절반을 차지.
*   **문제점:**
    *   `HR`, `Finance` 등으로 컴포넌트화가 시도되었으나, 여전히 `Firm` 클래스가 주식 시장 로직(`init_ipo`, `issue_shares`)을 직접 들고 있음.
    *   수많은 `@property`가 코드 가독성을 떨어뜨리고 클래스 길이를 불필요하게 늘림.

---

## 3. 리펙토링 제안 (Refactoring Proposal)

### 3.1. Simulation (`engine.py`) 분리 전략
*   **MarketManager 추출:** 시장 데이터 집계(`_prepare_market_data`)와 화폐 공급량 계산 로직을 전담하는 매니저 클래스 도입.
*   **EventScheduler 도입:** 틱별 이벤트(카오스, 선거 등)를 엔진 내부 하드코딩에서 별도의 스케줄러/이벤트 리스너 패턴으로 분리.
*   **MetricsCollector 분리:** SMA 계산, 버퍼 관리, 로깅 로직을 `EconomicIndicatorTracker` 또는 별도의 통계 수집기로 완전 이관.
*   **TransactionProcessor 강화:** 현재 `_process_stock_transactions` 등에 남아있는 거래 로직을 기존 `TransactionProcessor`로 완전히 통합.

### 3.2. Household (`core_agents.py`) 분리 전략 (Component Pattern)
*   **HouseholdEconomy:** 자산, 인벤토리, 포트폴리오, 세금 납부 로직을 캡슐화.
*   **HouseholdBiology:** 욕구(Needs), 나이, 건강, 생존 관련 로직 분리.
*   **HouseholdSocial:** 사회적 지위, 정치 성향, 관계(결혼 등) 로직 분리.
*   **HouseholdDecisionMaker:** `make_decision` 내의 절차적 로직을 별도의 Strategy 패턴으로 분리하여 의사결정 엔진과 연결.

### 3.3. Firm (`firms.py`) 분리 전략
*   **PublicListingManager (Finance 확장):** IPO, 주식 발행, 주가 관리, 시총 계산 로직을 `FinanceDepartment` 또는 별도의 상장 관리 컴포넌트로 이동.
*   **MarketStrategyComponent:** 섀도우 가격 계산(`_calculate_invisible_hand_price`) 및 마케팅 전략을 전담하는 컴포넌트 신설.
*   **Property Cleanup:** 단순 위임용 프로퍼티를 제거하고, 외부에서 `firm.hr.employees`와 같이 컴포넌트에 직접 접근하도록 인터페이스 변경 (또는 `__getattr__` 활용).

---

## 4. 기대 효과 (Expected Benefits)

1.  **테스트 용이성 (Testability):** 거대 클래스를 생성하지 않고도 개별 컴포넌트(예: `HouseholdEconomy`) 단위의 단위 테스트(Unit Test)가 가능해짐.
2.  **유지보수성 (Maintainability):** 특정 도메인(예: 세금 로직 변경) 수정 시, 해당 컴포넌트만 수정하면 되므로 사이드 이펙트 최소화.
3.  **인지 부하 감소 (Reduced Cognitive Load):** 개발자가 1,000줄이 넘는 코드를 읽지 않고도 관심 있는 로직(예: 300줄짜리 `MarketManager`)에 집중 가능.
4.  **협업 효율 증대:** 서로 다른 개발자가 `Biology`와 `Economy`를 동시에 작업할 때 충돌 발생 가능성 감소.

## 5. 결론 및 다음 단계

위 리펙토링은 한 번에 수행하기보다는 **점진적(Incremental)**으로 수행해야 합니다.
1.  **1단계:** `Simulation` 클래스에서 `Market Logic`을 추출하여 `MarketManager` 생성.
2.  **2단계:** `Household` 클래스의 경제 로직을 `EconomyComponent`로 이동.
3.  **3단계:** `Firm` 클래스의 주식 관련 로직을 `FinanceDepartment`로 완전히 이관.

이 제안서에 대한 팀의 검토와 승인을 요청합니다.
