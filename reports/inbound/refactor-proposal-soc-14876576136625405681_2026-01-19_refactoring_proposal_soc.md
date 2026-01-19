# SoC 리펙토링 제안서: God Class 분리 및 아키텍처 개선

## 1. 개요 (Overview)
본 문서는 시뮬레이션 엔진의 유지보수성, 확장성, 테스트 용이성을 확보하기 위해 주요 'God Class'를 식별하고, 관심사의 분리(SoC: Separation of Concerns) 원칙에 입각한 구체적인 리펙토링 방안을 제안합니다.

## 2. 현황 분석 (Current Status)
자체 개발한 정적 분석 도구(`analyze_classes.py`)를 사용하여 코드베이스를 스캔한 결과, `simulation` 패키지 내의 핵심 클래스들이 과도한 책임과 복잡도를 가지고 있음이 확인되었습니다.

### 주요 God Class 분석 결과

| 순위 | 클래스 (Class) | 파일 위치 (File Path) | 라인 수 (LOC) | 메서드 수 | 주요 문제점 (Issues) |
|:---:|---|---|---|---|---|
| **1** | **Household** | `simulation/core_agents.py` | **976** | 38 | 인구통계, 경제 활동, 심리 모델, 사회적 관계, 의사결정 로직이 단일 클래스에 강하게 결합됨. |
| **2** | **Simulation** | `simulation/engine.py` | **831** | 8 | 메인 루프 제어, 월드 상태 관리, 데이터 집계, 트랜잭션 처리, 초기화 로직이 혼재됨. |
| **3** | **Firm** | `simulation/firms.py` | **736** | 57 | 부서(Department) 객체로 일부 위임했으나, 하위 호환성을 위한 Wrapper 코드가 비대하며 IPO, M&A 로직 등이 추가됨. |

## 3. 리펙토링 제안 (Refactoring Proposal)

### 3.1. Simulation 클래스 (Engine)
**현재 문제점:**
*   **단일 책임 원칙 위반:** `Simulation` 클래스가 '시간의 흐름(Tick Loop)'과 '월드 상태(State Container)'를 모두 관리합니다.
*   **거대 메서드:** `run_tick` 메서드가 이벤트 실행, 에이전트 행동, 시장 매칭, 데이터 수집, 로그 출력을 순차적으로 모두 처리하여 가독성이 떨어집니다.

**개선 아키텍처 (Engine Decomposition):**
1.  **SimulationRunner (Driver)**: 시뮬레이션 루프(`while`), 정지 조건, 시간 진행만 담당합니다.
2.  **WorldState (Context)**: `agents`, `markets`, `government` 등 시뮬레이션의 모든 엔티티를 담는 데이터 컨테이너(Repository) 역할만 수행합니다.
3.  **TickScheduler (Orchestrator)**: `run_tick`의 로직을 단계별(Phase)로 나누어 실행 순서를 관리합니다.
    *   *Phase 1: Environment & Events*
    *   *Phase 2: Agent Decisions*
    *   *Phase 3: Market Clearing*
    *   *Phase 4: Resolution & Reporting*
4.  **TransactionProcessor**: 모든 거래(Transaction) 처리를 전담하는 별도 모듈로 완전 분리합니다.

### 3.2. Household 클래스 (Core Agents)
**현재 문제점:**
*   **기능의 파편화:** `update_needs`는 생물학적 욕구를, `decide_and_consume`은 경제적 소비를, `update_political_opinion`은 정치적 성향을 다루며 이들이 `Household` 클래스 내에 산재해 있습니다.
*   **확장성 부족:** 새로운 욕구 모델이나 행동 양식을 추가하려면 `Household` 클래스 자체를 수정해야 합니다.

**개선 아키텍처 (Component-Based System):**
`Household`는 껍데기(Shell) 역할만 하고, 실제 기능은 컴포넌트로 위임합니다.

1.  **BioComponent (생체 모듈)**: 나이, 성별, 건강, 배고픔, 에너지, 생존 욕구 처리.
2.  **EconComponent (경제 모듈)**: 자산(지갑), 인벤토리, 가계부(수입/지출), 임금 관리.
3.  **SocialComponent (사회 모듈)**: 가족 관계, 결혼, 친구, 사회적 지위(Rank), 정치 성향.
4.  **HousingComponent (주거 모듈)**: 주택 소유, 임대, 이사 결정 로직 (System 2 연동).
5.  **AgentBrain (Controller)**: `DecisionEngine`을 감싸고, 각 컴포넌트의 상태를 읽어 행동(Order)을 생성하는 두뇌 역할.

### 3.3. Firm 클래스 (Firms)
**현재 문제점:**
*   **불완전한 분리:** `hr`, `finance` 등 부서 객체가 도입되었으나, `firm.employees` 처럼 `Firm`이 직접 `hr.employees`를 중계하는 Wrapper 프로퍼티가 수십 개 존재하여 코드가 줄어들지 않았습니다.
*   **관심사 혼재:** 주식 시장 상장(IPO), 유상증자 로직, 브랜드 관리, M&A 방어 로직이 `Firm` 본체에 구현되어 있습니다.

**개선 아키텍처 (Full Departmentalization):**
1.  **Wrapper Property 제거**: 외부에서 `firm.hr.hire()`와 같이 명시적으로 부서에 접근하도록 변경 (Breaking Change 수용).
2.  **InventoryManager 신설**: 원자재/완제품 재고, 품질(Quality), 감가상각 관리를 전담.
3.  **InvestorRelations (IR Dept)**: 주식 발행, 자사주 매입, 배당 정책, 주주 명부 관리를 전담.
4.  **StrategyDept (System 2)**: M&A 결정, R&D 투자, 사업 확장 등 장기 전략 수립.

## 4. 기대 효과 (Expected Benefits)
1.  **테스트 용이성 (Testability)**: 거대한 `Household`를 생성하지 않고도 `EconComponent`만 따로 떼어내어 자산 로직을 테스트할 수 있습니다.
2.  **인지 부하 감소 (Reduced Cognitive Load)**: 개발자는 전체 시스템을 이해하지 않아도 특정 컴포넌트(예: `BioComponent`)만 집중해서 수정할 수 있습니다.
3.  **유연한 확장 (Extensibility)**: 새로운 기능(예: 질병 시스템) 도입 시 기존 코드를 건드리지 않고 `HealthComponent`를 추가/부착하는 방식으로 구현 가능합니다.

## 5. 실행 계획 (Action Plan)

### Phase 1: Firm Wrapper 제거 및 인터페이스 정리
*   **목표:** `Firm` 클래스 라인 수 400라인 이하로 축소.
*   **작업:** `firms.py` 내의 @property 제거, 호출부(`engine.py`, `dashboard` 등) 수정. `InvestorRelations` 컴포넌트 추출.

### Phase 2: Household 컴포넌트화
*   **목표:** `Household` 클래스를 단순 데이터 중계자로 전환.
*   **작업:** `BioComponent`, `EconComponent` 클래스 생성 및 로직 이동. 기존 `Household` 메서드는 컴포넌트 메서드 호출로 변경.

### Phase 3: Engine 모듈화
*   **목표:** `Simulation` 클래스의 책임을 루프 관리로 한정.
*   **작업:** `WorldState` 클래스 정의 및 상태 이관. `run_tick` 로직을 `Scheduler`로 분리.

---
**작성일:** 2026-01-19
**작성자:** Code Analysis Agent (Jules)