# 관심사 분리(SoC) 및 God Class 리팩토링 제안서

**작성일:** 2026년 1월 16일
**작성자:** AI Assistant (Jules)
**대상:** 시뮬레이션 엔진 아키텍처 팀

## 1. 개요 (Introduction)

현재 시뮬레이션 코드베이스에 대한 정적 분석 결과, 핵심 로직을 담당하는 일부 클래스들이 과도한 책임과 복잡도를 가지고 있는 'God Class' 형태를 띠고 있음이 확인되었습니다. 이는 유지보수성을 저하시키고, 테스트를 어렵게 하며, 새로운 기능 추가 시 사이드 이펙트 발생 가능성을 높입니다.

본 보고서는 Separation of Concerns (SoC) 원칙에 입각하여 주요 God Class를 식별하고, 이를 더 작고 응집도 높은 컴포넌트로 분리하기 위한 구체적인 리팩토링 방안을 제안합니다.

---

## 2. 분석 대상 및 현황 (Identified God Classes)

코드 라인 수(LOC)와 책임의 범위를 기준으로 다음 3개의 클래스를 리팩토링 최우선 대상으로 선정하였습니다.

| 클래스명 | 파일 위치 | LOC (약) | 주요 역할 |
|---|---|---|---|
| **Household** | `simulation/core_agents.py` | 1,078 | 가계의 경제, 생물학적 생존, 사회적 상호작용, 의사결정 등 |
| **Simulation** | `simulation/engine.py` | 1,042 | 시뮬레이션 초기화, 메인 루프, 시장 조율, 데이터 수집, 시스템 관리 |
| **Firm** | `simulation/firms.py` | 716 | 생산, 재무, 인사, 마케팅, 주식 시장 상호작용 (부분 컴포넌트화됨) |

---

## 3. 상세 분석 및 리팩토링 제안

### 3.1. Simulation 클래스 (`simulation/engine.py`)

#### 현황 및 문제점
`Simulation` 클래스는 현재 '모든 것의 관리자' 역할을 수행하고 있습니다.
- **초기화 로직 과부하:** 모든 에이전트, 시장, 시스템의 생성 및 연결을 담당.
- **메인 루프 복잡도:** `run_tick` 메서드 내에서 경제 지표 계산, 정책 실행, 에이전트 행동 트리거, 데이터 로깅이 뒤섞여 있음.
- **데이터 수집 로직 혼재:** 시뮬레이션 흐름 제어와 통계 데이터 수집(Tracker) 호출이 강하게 결합됨.

#### 리팩토링 제안: 책임 분산 (Orchestration Decomposition)

1.  **`SimulationEngine` (Core Loop):** 오직 시간(`tick`) 진행과 각 단계(Phase)별 실행 순서만 관리하는 순수 스케줄러로 축소.
2.  **`AgentLifecycleManager` (기존 존재, 강화 필요):** 에이전트의 생성, 사망, 상속, 분리(Mitosis) 로직을 전담. `Simulation`에서 `spawn_firm`, `process_death` 등의 로직을 완전히 이관.
3.  **`MarketEngine` (New):** 모든 시장(`Markets`)의 주문 처리(`match_orders`), 청산(`clear_orders`), 가격 업데이트 로직을 캡슐화. `Simulation`은 `market_engine.resolve_all()` 한 번만 호출.
4.  **`DataCollector` / `SimulationMetrics`:** `tracker`와 로깅 관련 로직을 통합 관리. `Simulation` 클래스 내의 버퍼(`inflation_buffer` 등)와 통계 계산 로직을 이동.
5.  **`EventScheduler` (New):** 특정 틱(Chaos Event, Election 등)에 발생하는 이벤트를 정의하고 실행하는 모듈. 하드코딩된 `if self.time == 200:` 같은 로직 제거.

---

### 3.2. Household 클래스 (`simulation/core_agents.py`)

#### 현황 및 문제점
`Household`는 '인간'의 모든 측면을 하나의 클래스에 담고 있습니다.
- **다중 인격:** 경제적 주체(노동/소비)이면서 동시에 생물학적 주체(나이/생존)이고, 사회적 주체(정치/관계)임.
- **상태 과부하:** `inventory`, `skills`, `needs`, `political_opinion`, `social_rank` 등 성격이 다른 데이터가 플랫하게 존재.
- **로직 혼재:** `make_decision` 내부에서 주택 구매 로직, 임금 계산 로직(`shadow_wage`), 소비 결정 로직이 섞여 있음.

#### 리팩토링 제안: 컴포넌트 기반 아키텍처 (Component-Based Entity)

1.  **`HouseholdEconomy` (Component):**
    *   책임: 자산(`assets`), 인벤토리(`inventory`), 가계부(수입/지출), 세금 납부.
    *   이동 메서드: `consume`, `pay_taxes`, `adjust_assets`, `inventory` 관리.
2.  **`HouseholdBiology` (or `Demographics` 강화):**
    *   책임: 나이, 성별, 생존 욕구(`needs['survival']`), 사망 체크.
    *   현재 `DemographicsComponent`가 있으나, `Household` 자체에 여전히 `age`, `needs` 관련 로직이 남아있으므로 이를 완전히 위임.
3.  **`HouseholdSocial` (Component):**
    *   책임: 정치 성향(`political_opinion`), 사회적 지위(`social_status`), 인맥/관계.
    *   이동 속성: `approval_rating`, `social_rank`, `conformity`.
4.  **`HouseholdLabor` (Component):**
    *   책임: 직업 상태(`is_employed`), 임금(`wage`), 기술(`skills`), 구직/이직 활동.
    *   `LaborManager`가 존재하나, `Household`에 여전히 `shadow_reservation_wage` 등의 로직이 존재함. 이를 `LaborStrategy` 등으로 캡슐화.

---

### 3.3. Firm 클래스 (`simulation/firms.py`)

#### 현황 및 문제점
`Firm` 클래스는 `HRDepartment`, `FinanceDepartment` 등으로 부분적인 리팩토링이 진행되었으나, 여전히 **'Leaky Abstraction'** 문제가 심각합니다.
- **Legacy Property Hell:** 하위 컴포넌트(`hr`, `finance`)의 속성을 `Firm`의 속성인 것처럼 노출하기 위해 수십 개의 `@property`와 setter가 존재하여 코드를 비대하게 만듦.
- **비즈니스 로직 잔존:** `calculate_valuation`, `liquidate_assets`, `produce` 등 핵심 로직이 컴포넌트가 아닌 `Firm` 클래스에 직접 구현되어 있음.
- **Shadow Mode 혼재:** `_calculate_invisible_hand_price`와 같은 실험적/분석적 로직이 핵심 비즈니스 로직과 섞여 있음.

#### 리팩토링 제안: 완전한 위임 (Strict Delegation) & Facade 패턴

1.  **Legacy Property 제거:** `firm.employees` 대신 `firm.hr.employees`와 같이 명시적으로 컴포넌트에 접근하도록 호출부 수정 (단기적으로는 Deprecation Warning 추가).
2.  **`StrategyDepartment` (New):**
    *   책임: `make_decision`의 의사결정 로직, `Shadow Mode` 가격/임금 책정 로직, IPO/상장 관련 전략.
    *   현재 `Firm`에 있는 `calculate_valuation`, `init_ipo` 등을 이동.
3.  **`ProductionManager` (강화):**
    *   `produce` 메서드의 로직을 완전히 `ProductionDepartment`로 이동하고, `Firm`은 단순 호출만 수행.
4.  **`BrandManager` 통합:**
    *   현재 별도 클래스이나 `Firm`과 강하게 결합됨. `SalesDepartment` 또는 `MarketingDepartment`로 명확히 계층화.

---

## 4. 실행 로드맵 (Roadmap)

1.  **Phase 1 (준비):** 각 클래스에 대한 Unit Test 커버리지 확보 (리팩토링 시 기능 파손 방지).
2.  **Phase 2 (Firm):** `Firm` 클래스의 Legacy Property 제거 및 `StrategyDepartment` 신설.
3.  **Phase 3 (Simulation):** `MarketEngine` 분리 및 `run_tick` 메서드 다이어트.
4.  **Phase 4 (Household):** `HouseholdEconomy` 컴포넌트 추출 및 상태 데이터 마이그레이션.

위 제안을 통해 각 클래스의 코드 라인을 300~500줄 이하로 줄이고, 각 모듈의 역할(Role)을 명확히 하여 시스템의 안정성과 확장성을 확보할 수 있습니다.