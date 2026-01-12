# 리펙토링 제안서: 관심사의 분리 (Separation of Concerns)

**작성일:** 2026년 1월 12일
**작성자:** Jules (Software Engineer)

## 1. 개요 (Executive Summary)

현재 경제 시뮬레이션 프로젝트는 기능이 확장됨에 따라 일부 핵심 클래스들의 복잡도가 급격히 증가했습니다. 특히 `Simulation`, `Household`, `Firm` 등 주요 에이전트 및 엔진 클래스가 여러 역할(경제 활동, 생애 주기, 사회적 상호작용, 데이터 집계 등)을 동시에 수행하고 있어 "God Class"의 형태를 띠고 있습니다.

본 보고서는 "관심사의 분리(Separation of Concerns, SoC)" 원칙에 입각하여 리펙토링이 필요한 클래스를 식별하고, 이를 개선하기 위한 구체적인 아키텍처 변경안을 제안합니다.

## 2. 식별된 God Class 및 문제점 분석

### 2.1. `Simulation` (in `simulation/engine.py`) - **최우선 리펙토링 대상**

*   **현재 상태:** 약 800라인 이상의 코드로 구성되어 있으며, 시뮬레이션의 모든 것을 관장합니다.
*   **주요 위반 사항 (Violations):**
    *   **Transaction Processing:** `_process_transactions` 메서드 내에서 세금 계산, 상품별 특수 로직(서비스 vs 재화), 품질 혼합 로직, 주식 거래 처리 등을 모두 수행합니다.
    *   **Lifecycle Management:** `_handle_agent_lifecycle` 메서드에서 에이전트의 사망, 파산, 상속 로직을 직접 제어합니다.
    *   **Orchestration vs Implementation:** 루프를 돌리는 역할(Orchestrator)뿐만 아니라, 시장을 순회하며 주문을 매칭하고 데이터를 수집하는 세부 구현까지 포함하고 있습니다.
    *   **System Glue:** DemographicManager, ImmigrationManager, HousingSystem 등 수많은 하위 시스템을 직접 생성하고 연결하는 "거대한 접착제" 역할을 합니다.

### 2.2. `Household` (in `simulation/core_agents.py`)

*   **현재 상태:** 가계 에이전트의 상태와 행동을 모두 포함하며, 생물학적, 경제적, 사회적 로직이 혼재되어 있습니다.
*   **주요 위반 사항 (Violations):**
    *   **Complex Consumption Logic:** `decide_and_consume` 및 `consume` 메서드가 인벤토리 관리, 효용 계산, 내구재 설치, 교육 XP 획득 등 너무 많은 부수 효과(Side Effects)를 처리합니다.
    *   **Mixed State:** 생물학적 상태(나이, 성별), 경제적 상태(자산, 인벤토리), 사회적 상태(정치 성향, 지위), 심리적 상태(욕구)가 하나의 클래스 플랫하게 펼쳐져 있습니다.
    *   **Leisure & Housing Integration:** `decide_housing`과 같은 System 2(장기 계획) 로직이 에이전트 클래스 내부에 직접 구현되어 있습니다.

### 2.3. `Firm` (in `simulation/firms.py`)

*   **현재 상태:** 생산, 재무, 인사, 마케팅 로직이 `Firm` 클래스 하나에 집중되어 있습니다.
*   **주요 위반 사항 (Violations):**
    *   **Production & Inventory:** `produce` 메서드가 Cobb-Douglas 생산 함수 계산과 원자재 차감, 품질 갱신을 동시에 수행합니다.
    *   **HR Management:** `update_needs` 메서드 내에서 임금 지급, 해고(구조조정), 퇴직금 계산 로직이 수행됩니다. 이는 "Need Update"라는 메서드 명과도 맞지 않는 역할입니다.
    *   **Financial Logic:** 배당 지급(`distribute_dividends`), 주식 발행, 세금 납부 로직이 섞여 있습니다.

### 2.4. `Government` (in `simulation/agents/government.py`)

*   **현재 상태:** 재정 정책(세금/보조금), 정치(선거), 복지 로직이 혼재되어 있습니다.
*   **주요 위반 사항 (Violations):**
    *   **Fiscal Calculation:** 소득세 구간 계산 로직(`calculate_income_tax`)과 같은 "비즈니스 로직"이 에이전트 상태 관리에 포함되어 있습니다.
    *   **Political Coupling:** 선거 로직(`check_election`)과 지지율 업데이트 로직이 재정 정책 실행 로직과 강하게 결합되어 있습니다.

---

## 3. 리펙토링 제안 (Refactoring Proposals)

### 3.1. `Simulation` 클래스 분해: "엔진의 모듈화"

`Simulation` 클래스는 오직 "조율자(Coordinator)" 역할만 수행해야 합니다.

*   **제안 1: `TransactionProcessor` 추출**
    *   `_process_transactions`의 로직을 별도 클래스로 분리합니다.
    *   각 거래 타입(Goods, Labor, Financial, RealEstate)별로 처리 전략(Strategy Pattern)을 적용합니다.
    *   *효과:* 세금 로직이나 재고 처리 로직 변경 시 엔진 코드를 건드리지 않아도 됩니다.

*   **제안 2: `LifecycleOrchestrator` 강화**
    *   현재 `_handle_agent_lifecycle` 로직을 `DemographicManager` 및 `CorporateManager`로 완전히 이관하거나, 이를 조율하는 전용 매니저를 둡니다.
    *   *효과:* 에이전트의 생성과 소멸 로직이 엔진 루프에서 분리되어 명확해집니다.

*   **제안 3: `MarketSystem` 도입**
    *   `markets` 딕셔너리를 순회하며 매칭하는 로직을 `MarketSystem` 클래스로 캡슐화합니다.
    *   `simulation.market_system.step(tick)` 형태로 호출합니다.

### 3.2. `Household` 및 `Firm`: "컴포넌트 기반 아키텍처 (Entity-Component)"

에이전트 클래스가 비대해지는 것을 막기 위해, 기능을 컴포넌트로 분리하고 에이전트는 이를 소유(Composition)하는 형태로 변경합니다.

*   **제안 1: `InventoryComponent`**
    *   `inventory`, `input_inventory`, `inventory_quality` 관리 로직을 분리합니다.
    *   `consume`, `add`, `remove` 메서드를 제공하여 수량과 품질을 관리합니다.

*   **제안 2: `HRDepartment` (for Firm)**
    *   `Firm`의 직원 관리(`employees`, `employee_wages`), 임금 지급, 채용/해고 로직을 담당하는 컴포넌트입니다.
    *   `firm.hr.pay_wages()`, `firm.hr.fire_employee()` 형태로 사용합니다.

*   **제안 3: `FinanceDepartment` (for Firm)**
    *   주식 발행, 배당 결정, 자금 조달, 세금 납부 등을 담당합니다.
    *   `firm.finance.distribute_dividends()`

*   **제안 4: `DemographicsComponent` (for Household)**
    *   나이, 성별, 결혼 상태, 자녀 목록 등 인구통계학적 데이터를 관리합니다.

### 3.3. `Government`: "기능별 부처 분리"

*   **제안 1: `TaxationAuthority` (국세청)**
    *   세금 구간 계산, 징수 로직을 전담합니다. `Government` 에이전트는 정책(세율)만 결정하고, 계산은 이 모듈에 위임합니다.

*   **제안 2: `WelfareAdministration` (복지부)**
    *   보조금 지급 대상을 선별하고 집행하는 로직을 분리합니다.

## 4. 기대 효과 (Expected Benefits)

1.  **테스트 용이성 (Testability):** 거대 클래스를 인스턴스화하지 않고도, `TransactionProcessor`나 `HRDepartment` 등 개별 모듈만 단위 테스트하기 쉬워집니다.
2.  **유지보수성 (Maintainability):** 특정 로직(예: 세금 계산 방식 변경)을 수정할 때, 관련된 작은 파일 하나만 수정하면 되므로 사이드 이펙트가 줄어듭니다.
3.  **확장성 (Extensibility):** 새로운 기능(예: 새로운 세금 유형, 새로운 노동 계약 형태) 추가 시 기존 코드를 덜 건드리고 컴포넌트를 교체하거나 확장하는 방식으로 대응 가능합니다.

## 5. 결론

현재 시스템은 초기 프로토타입 단계를 지나 복잡한 경제 모델로 진화했습니다. 향후 안정적인 기능 확장을 위해서는 위에서 제안한 **God Class 해체 및 컴포넌트화** 작업이 필수적입니다. 우선적으로 `Simulation` 클래스의 트랜잭션 처리 로직 분리와 `Firm` 클래스의 HR/Finance 기능 분리를 권장합니다.
