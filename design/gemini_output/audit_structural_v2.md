# [AUDIT-STRUCTURAL-V2] 구조적 결함 및 누출된 추상화 전수 조사

## 1. God Class 위험군 리스트
코드베이스 전수 조사 결과, 다음 파일들이 구조적 복잡도와 크기 면에서 위험군으로 식별되었습니다.

*   **`simulation/core_agents.py` (900 lines) - CRITICAL**
    *   **이유:** 단일 파일 코드 라인 수가 800줄을 초과합니다. `Household` 클래스가 Bio, Econ, Social 컴포넌트를 위임받고 있음에도 불구하고, Facade 메서드와 레거시 속성들이 과도하게 집중되어 있습니다.
    *   **Inheritance:** `Household` -> `BaseAgent` -> `IFinancialEntity` (추정). 상속 깊이보다는 클래스 자체의 책임 범위(Blob)가 문제입니다.

*   **`simulation/db/repository.py` (745 lines) - WARNING**
    *   **이유:** 800줄 제한에 근접하고 있습니다. 데이터 저장 로직이 모든 엔티티(Agent, Market, Transaction, Macro)에 대해 단일 파일에 집중되어 있어, 향후 스키마 확장에 병목이 될 수 있습니다.

*   **`simulation/tick_scheduler.py` (708 lines) - WARNING**
    *   **이유:** 메인 루프 로직이 매우 비대합니다. 단순한 스케줄링을 넘어, 각 단계의 세부 로직(학습 업데이트, 센서 데이터 처리 등)이 절차적으로 나열되어 있습니다.

## 2. Leaky Abstraction 위반 지점/라인 전체 목록
`make_decision` 메서드 호출과 `DecisionContext` 사용, 그리고 객체 참조와 관련된 누출 지점들입니다.

### A. Decision Context & Engine Leaks
*   **`simulation/components/hr_department.py` (Line ~92)**
    *   `_handle_insolvency` 메서드 내에서 로그 기록을 위해 `self.firm.decision_engine.context.current_time`에 접근합니다.
    *   **위반 내용:** 컴포넌트(`HRDepartment`)가 상위 에이전트(`Firm`)의 `decision_engine` 내부 상태(`context`)에 역방향으로 접근하고 있습니다. `context`는 의사결정 시점의 transient 객체여야 하는데, 이를 상태처럼 접근하는 것은 결합도를 높입니다.

*   **`simulation/tick_scheduler.py` (Multiple Lines)**
    *   `run_tick` 메서드 내에서 `firm.decision_engine.ai_engine` 및 `household.decision_engine.ai_engine`에 반복적으로 직접 접근합니다.
    *   **위반 내용:** Law of Demeter 위반. 스케줄러가 에이전트의 의사결정 엔진의 *내부 구현(AI Engine)*까지 알고 있습니다. `ILearningAgent` 인터페이스를 통해 학습 업데이트를 추상화해야 합니다.

*   **`simulation/core_agents.py` & `simulation/firms.py`**
    *   `decision_engine.loan_market = loan_market`
    *   **위반 내용:** 의사결정 엔진에 `Market` 객체(LoanMarket)를 직접 주입하고 있습니다. Purity Gate 원칙상, 시장 접근은 `make_decision` 시점에 `DecisionContext`를 통해서만 이루어져야 하며, 엔진이 시장 객체를 멤버 변수로 보유(Stateful)하는 것은 피해야 합니다.

### B. DTO Usage
*   대부분의 `make_decision` 호출(`Firm`, `Household`)은 `state_dto`를 생성하여 `DecisionContext`에 담아 전달하고 있어 **양호**합니다.
*   그러나 `AIDrivenHouseholdDecisionEngine`에서 `HousingManager`를 초기화할 때 `HouseholdStateDTO`를 넘기고 있는데, 이는 `HousingManager`가 DTO에 의존하도록 리팩토링된 상태라 **정상**입니다.

## 3. Sequence Check (Tick Scheduler)
명세서의 **Decisions -> Matching -> Transactions -> Lifecycle** 순서 준수 여부를 확인했습니다.

### 발견된 우회(Bypass) 및 순서 위반
1.  **Post-Tick Logic에서의 생산 및 세금 납부 (CRITICAL)**
    *   **위치:** `tick_scheduler.py`의 `run_tick` 메서드 하단 (Lifecycle 이후).
    *   **내용:** `firm.produce()`와 `firm.update_needs()`가 호출되고, `update_needs` 내부에서 `finance.pay_taxes()`가 호출됩니다. 이 과정에서 `settlement_system.transfer()`가 실행됩니다.
    *   **위반:** **Transaction Phase**(`_phase_transactions`)가 이미 종료된 후에 발생하는 거래입니다. 이는 `TransactionProcessor`의 일괄 처리를 우회하며, 원자성 보장이나 통계 집계에서 누락될 위험이 있습니다.

2.  **Pre-Decision Profit Distribution**
    *   **위치:** `tick_scheduler.py`의 `run_tick` 상단 (Decisions 이전).
    *   **내용:** `firm.distribute_profit()`가 호출되어 배당금이 지급됩니다.
    *   **위반:** **Transaction Phase**가 아닌 시점에 자산 이전이 발생합니다. 모든 자산 변동(거래)은 Transaction Phase에 집중되어야 합니다.

## 4. 아키텍처 부채 상환 우선순위 제안

1.  **[High Priority] Tick Scheduler 순서 정규화**
    *   `firm.produce`, `update_needs` (세금), `distribute_profit` (배당) 로직을 정해진 Phase(`Decisions` 또는 별도의 `Pre-Processing`, `Post-Processing` 페이즈이나 거래는 반드시 `Transactions` 페이즈) 안으로 이동시켜야 합니다.
    *   특히 모든 `SettlementSystem.transfer` 호출은 `_phase_transactions` 내에서 처리되거나, 적어도 해당 페이즈가 열려있는 동안에만 발생하도록 구조를 변경해야 합니다.

2.  **[High Priority] God Class 분할 (`core_agents.py`)**
    *   `Household` 클래스를 `simulation/agents/household.py`로 분리하고, `core_agents.py`를 제거하거나 `base_agent.py` 등으로 역할을 축소해야 합니다.

3.  **[Medium Priority] HRDepartment 역참조 제거**
    *   `HRDepartment.process_payroll` 메서드에 `current_time` 인자를 명시적으로 전달하고, 로그 기록 시 `context` 객체를 탐색하지 않도록 수정해야 합니다.

4.  **[Medium Priority] Scheduler의 Demeter 법칙 준수**
    *   `firm.decision_engine.ai_engine` 접근을 `firm.update_learning()` 내부로 완전히 캡슐화하고, 외부에서는 AI 엔진의 존재를 모르도록 리팩토링해야 합니다.
