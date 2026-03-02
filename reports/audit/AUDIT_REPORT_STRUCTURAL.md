# AUDIT_REPORT_STRUCTURAL: Structural Integrity Audit (v2.0)

**목표**: 이후 확립된 'DTO 기반 디커플링' 및 'Component SoC' 아키텍처가 실제 코드베이스에서 엄격히 준수되고 있는지 기술적으로 검증한다.

## 1. 용어 정의 (Terminology)
- **God Class**: 단일 클래스가 800라인 이상의 물리적 코드를 소유하거나, 분리 가능한 도메인 책임(예: 가계의 생존 로직과 주식 포트폴리오 로직)을 3개 이상 혼합하여 소유한 상태.
- **Leaky Abstraction (누출된 추상화)**: DTO(Data Transfer Object)를 사용해야 하는 구간(예: `DecisionContext`)에서 에이전트 객체(`Household`, `Firm`)의 인스턴스를 직접 전달하여 객체의 내부 상태를 외부 모듈에 노출시키는 행위.
- **Sacred Sequence (신성한 시퀀스)**: 시뮬레이션 틱 내에서 `Decisions -> Matching -> Transactions -> Lifecycle`로 이어지는 불변의 실행 순서.
- **Purity Gate**: 에이전트의 내부 필드(예: `_assets`)에 접근하기 위해 반드시 거쳐야 하는 프로퍼티 또는 컴포넌트 메서드.

## 2. 논리 전개 (Logical Flow)
정적 스캔 및 코드 분석 결과 다음과 같은 위반 사항이 발견되었다.

### 2.1 God Classes 식별 (800+ lines)
파일 크기 및 물리적 코드 스캔을 통해 다음의 God Class들이 식별되었다.
*   **`simulation/firms.py`**: `Firm` (1765 lines)
    *   도메인 책임이 과도하게 집중되어 있으며 생산, 마케팅, 재무 등 분리 가능한 부서가 하나로 뭉쳐있을 가능성이 높다.
*   **`simulation/core_agents.py`**: `Household` (1181 lines)
    *   생존 로직, 소비 로직, 투자 포트폴리오 로직 등이 하나의 클래스에 혼합되어 있어 분리가 필요하다.
*   **`simulation/systems/settlement_system.py`**: `SettlementSystem` (966 lines)
    *   시스템 컴포넌트임에도 800라인이 넘는 방대한 로직을 포함하고 있어, 거래 처리, 회계 기록 등의 로직 분리가 요구된다.

### 2.2 Abstraction Leaks (Raw Agent Leaks) 식별
의사결정 엔진 및 서비스 영역에서 DTO 대신 원시 에이전트 객체(`List[Any]`, `List[IAgent]`)를 직접 전달하여 객체의 내부 상태가 노출되는 누출된 추상화 사례가 다수 발견되었다.
*   **`modules/government/api.py`**
    *   `run_welfare_check` 메서드에서 `agents: List[IAgent]`를 파라미터로 받고 있어 에이전트 인터페이스가 직접 노출됨.
*   **`modules/government/services/welfare_service.py`**
    *   `run_welfare_check` 메서드 구현부에서 `agents: List[IAgent]`를 받고 있음.
*   **`modules/government/engines/execution_engine.py`**
    *   `execute` 메서드에서 `agents: List[Any]`를 받음.
    *   `_execute_social_policy` 메서드에서 `agents: List[Any]`를 받음.
    *   `_execute_firm_bailout` 메서드에서 `agents: List[Any]`를 받음.
*   **`simulation/agents/government.py`**
    *   `run_welfare_check` 메서드에서 `agents: List[Any]`를 받음.
    *   `execute_social_policy` 메서드에서 `agents: List[Any]`를 받음.
    *   `run_public_education` 메서드에서 `agents: List[Any]`를 받음.

## 3. 구체적 방법 예시 (Concrete Examples)
발견된 문제점들에 대한 구조적 개선 방법은 다음과 같다.

- **God Class 리팩토링 예시**:
  `Firm` 클래스 내에 존재하는 여러 로직을 `ProductionDepartment`, `SalesDepartment`, `FinanceDepartment` 등과 같이 별도의 컴포넌트 클래스로 분리하고 의존성을 주입받아 사용하도록 수정해야 한다.
- **Abstraction Leak 개선 예시**:
  의사결정 엔진이나 서비스(예: `WelfareService.run_welfare_check`, `PolicyExecutionEngine.execute`)에 파라미터를 넘길 때 원시 에이전트 객체 목록(`List[Any]`, `List[IAgent]`)이 아닌 에이전트의 상태를 담은 DTO 리스트(예: `List[AgentStateDTO]`)를 전달하도록 시그니처와 구현을 수정해야 한다.

## 4. 구조적 모듈 현황 진단
*   **메인 구조 (Simulation -> System -> Component) 위반**: `Firm`, `Household` 등 주요 에이전트 객체들이 Component 레벨로 세분화되지 못하고 거대한 God Class로 남아 있어, 각 도메인 책임의 독립적인 테스트가 매우 어려운 상태이다.
*   **모듈 간 결합도 상승**: 정부 모듈(`modules/government`)의 의사결정 엔진 및 서비스들이 원시 에이전트 객체에 직접 의존함으로써, 에이전트 내부 구현 변경이 다른 모듈(정부 모듈 등)의 테스트 실패나 사이드 이펙트로 이어질 수 있는 강한 결합도를 보이고 있다. 이는 DTO 기반 디커플링 원칙에 정면으로 위배된다.

## 5. Output Configuration
- **Output Location**: `reports/audit/AUDIT_REPORT_STRUCTURAL.md`
