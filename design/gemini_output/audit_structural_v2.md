# [AUDIT-STRUCTURAL-V2] 구조적 결함 및 누출된 추상화 전수 조사 보고서

## 1. [God Class 위험군 리스트]

**기준**: 800라인 초과 파일 및 상속 깊이 4단계 이상.

*   **`simulation/core_agents.py` (Household Agent)**
    *   **Line Count**: 1003 lines (위험 기준 800라인 초과).
    *   **Description**: `Household` 클래스는 초기화, 의사결정 위임, 상태 어댑터, 소비 로직, 라이프사이클 관리(노화, 복제) 등을 모두 포함하고 있어 "God Class"로 분류됩니다.
    *   **Inheritance Depth**: `Household` -> `BaseAgent` -> `ABC` (Depth 2). 상속 깊이는 기준 미달이나 클래스 비대화가 심각함.

*   **`simulation/orchestration/phases.py`**
    *   **Line Count**: 792 lines (경계선).
    *   **Risk**: 페이즈 관리 로직이 집중되어 있어 향후 리스크가 될 수 있음.

*   **`simulation/agents/government.py` (Government Agent)**
    *   **Line Count**: 716 lines.
    *   **Risk**: 정책 결정, 세금 징수, 재정 관리 로직이 혼재되어 있어 향후 비대화 가능성 높음.

## 2. [Leaky Abstraction 위반 지점/라인 전체 목록]

**기준**: `make_decision` 메서드에 `self` 전달 혹은 `DecisionContext` 생성 시 DTO가 아닌 에이전트 객체 직접 할당.

### A. Method Signature Leaks (Agent Interface Level)
`DecisionContext` 내부가 아닌, `make_decision` 메서드 시그니처 자체에서 Raw Agent(`government`)를 인자로 받아 내부 로직으로 전달하는 누출이 발견되었습니다.

*   **File**: `simulation/core_agents.py`
    *   **Class**: `Household`
    *   **Method**: `make_decision`
    *   **Violation**: `def make_decision(..., government: Optional[Any] = None, ...)`
    *   **Details**: `government` 인자가 Raw Agent 객체로 전달됩니다. 이는 `DecisionContext`의 Purity 원칙(DTO only)을 우회하여 Agent 내부 메서드(`_execute_internal_order` 등)로 흘러들어갈 수 있는 경로를 제공합니다.

*   **File**: `simulation/firms.py`
    *   **Class**: `Firm`
    *   **Method**: `make_decision`
    *   **Violation**: `def make_decision(..., government: Optional[Any] = None, ...)`
    *   **Details**: 위와 동일. `_execute_internal_order` 메서드에서 `government` 객체를 사용하여 세금 납부(`pay_ad_hoc_tax`) 등을 수행할 때 Raw Agent에 접근합니다.

### B. DecisionContext Purity (Clean)
다행히 `DecisionContext`의 생성 및 Decision Engine으로의 전달 과정은 DTO 패턴을 잘 따르고 있습니다.
*   `DecisionContext` 정의(`simulation/dtos/api.py`)는 `state: Union[HouseholdStateDTO, FirmStateDTO]`와 `government_policy: Optional[GovernmentPolicyDTO]`를 사용하여 타입 레벨에서 격리되어 있습니다.
*   `Firm` 및 `Household`에서 `DecisionContext` 생성 시 `self.get_state_dto()` 등을 통해 DTO를 변환하여 주입하고 있습니다.

## 3. [Sequence Check]

**기준**: Decisions -> Matching -> Transactions -> Lifecycle 순서 준수 여부.

**분석 대상**: `simulation/orchestration/tick_orchestrator.py`

**실제 실행 순서 (`run_tick`)**:
1.  `Phase0_PreSequence`
2.  `Phase_Production`
3.  **`Phase1_Decision` (Decisions)**
4.  **`Phase_Bankruptcy` (Lifecycle - Firm Death)**  <-- **VIOLATION**
5.  `Phase_SystemicLiquidation` (Lifecycle - Systemic)
6.  **`Phase2_Matching` (Matching)**
7.  **`Phase3_Transaction` (Transactions)**
8.  **`Phase_Consumption` (Lifecycle - Household Aging/Needs)**
9.  `Phase5_PostSequence`

**위반 사항**:
*   **Firm Lifecycle (Bankruptcy) Timing**: 기업의 파산 처리(`Phase_Bankruptcy`)가 **Matching 및 Transactions 이전**에 수행됩니다.
    *   요구사항: Decisions -> Matching -> Transactions -> Lifecycle
    *   현황: Decisions -> Lifecycle(Bankruptcy) -> Matching -> Transactions
    *   **문제점**: 의사결정을 내린 직후 거래를 시도해보기도 전에 파산 처리가 먼저 발생합니다. 이는 "거래를 통해 회생할 기회"를 박탈하거나, 시뮬레이션 논리상 "결과(Transaction)에 따른 상태 변화(Lifecycle)"라는 인과관계를 역행합니다.

*   **Household Lifecycle (Consumption/Aging)**:
    *   `Phase_Consumption` (Step 8)에서 수행되므로 Transactions 이후에 위치하여 요구사항을 준수합니다.

## 4. [아키텍처 부채 상환 우선순위 제안]

1.  **Priority 1: `Household` God Class Refactoring (High Impact)**
    *   `Household` 클래스(1003 lines)를 더 작은 컴포넌트(`BioComponent`, `EconComponent` 등)로 분리하는 작업이 진행 중인 것으로 보이나, 여전히 메인 파일이 너무 큽니다. `update_needs`, `make_decision` 내의 로직을 컴포넌트로 완전히 위임하여 메인 클래스는 껍데기(Facade) 역할만 하도록 리팩토링해야 합니다.

2.  **Priority 2: Fix Firm Bankruptcy Sequence (High Risk)**
    *   `Phase_Bankruptcy`를 `Phase3_Transaction` 이후로 이동시켜야 합니다. 기업은 거래(매출 발생) 결과를 바탕으로 자금 부족 여부를 판단하고 파산해야 합니다. 현재 순서는 의사결정만 하고 매출 기회 없이 파산시키는 구조입니다.

3.  **Priority 3: Seal `make_decision` Abstraction Leak (Medium Impact)**
    *   `make_decision` 메서드 시그니처에서 `government` (Raw Agent) 인자를 제거해야 합니다.
    *   대신 `DecisionContext`에 포함된 `government_policy` DTO나 `market_snapshot`을 활용하도록 변경하고, 내부적으로 `government` 객체가 필요한 로직(`pay_tax` 등)은 `Transaction` 객체를 생성하여 반환하는 방식(Intent-based)으로 변경해야 합니다. (현재는 즉시 실행 방식인 `_execute_internal_order`가 혼재되어 있음).
