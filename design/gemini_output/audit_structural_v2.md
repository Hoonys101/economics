# Structural Audit V2 Report

## [God Class 위험군 리스트]

파일 크기(800라인 이상) 기준으로 식별된 위험군은 다음과 같습니다. 상속 계층 깊이는 모두 얕은 수준(2단계 이하)으로 양호하나, 클래스 내 책임 집중(Cohesion 저하)이 우려됩니다.

| 파일 경로 | 라인 수 | 클래스 | 상속 깊이 | 설명 |
|---|---|---|---|---|
| `simulation/core_agents.py` | 997 | `Household` | 2 (BaseAgent, ILearningAgent) | `Bio`, `Econ`, `Social` 컴포넌트로 위임하고 있으나, Facade 클래스 자체가 비대함. 특히 Getter/Setter와 어댑터 로직이 과도하게 집중됨. |
| `simulation/tick_scheduler.py` | 943 | `TickScheduler` | 1 | 시뮬레이션의 모든 단계(Phase 0~4, Post-Tick)를 관장하며 God Object화 진행 중. 트랜잭션 생성, 로깅, 예외 처리 로직이 혼재됨. |

## [Leaky Abstraction 위반 지점/라인 전체 목록]

`make_decision` 메서드 호출 시 에이전트 인스턴스(`self`)를 직접 전달하거나, `DecisionContext` 생성 시 에이전트를 주입하는 코드를 전수 조사하였으나, **위반 사항이 발견되지 않았습니다.**

현재 코드베이스는 다음과 같이 DTO 패턴을 준수하고 있습니다:
*   **Household**: `self.create_state_dto()`를 통해 `HouseholdStateDTO` 생성 후 Context에 주입.
*   **Firm**: `self.get_state_dto()`를 통해 `FirmStateDTO` 생성 후 Context에 주입.
*   **Decision Engine**: `context`와 `macro_context`만을 인자로 받으며, Agent 객체에 직접 접근하지 않음.

## [아키텍처 부채 상환 우선순위 제안]

식별된 구조적 문제와 Tick Scheduler의 시퀀스 분석을 바탕으로 다음 우선순위를 제안합니다.

### 1순위: Tick Scheduler 분해 (Phase Strategy Pattern 도입)
*   **현상**: `tick_scheduler.py`가 943라인에 달하며, `Pre-Sequence`, `Transaction Generation`, `Sacred Sequence (Phases 1-4)`, `Post-Tick` 로직이 한 파일에 섞여 있음.
*   **제안**: 각 단계(`_phase_decisions`, `_phase_matching` 등)를 독립된 클래스(`DecisionPhase`, `MatchingPhase` 등)로 분리하고, Scheduler는 이를 실행하는 역할만 수행하도록 리팩토링.

### 2순위: Lifecycle Phase 통합 (Firm Update Needs 이동)
*   **현상**: 시퀀스 점검 결과, `Decisions -> Matching -> Transactions -> Lifecycle` 순서는 지켜지고 있으나, `firm.update_needs` (Aging, Bankruptcy Check)가 Phase 4 (`Lifecycle`)가 아닌 `Post-Tick Logic`에서 실행되고 있음.
*   **제안**: `firm.update_needs` 로직을 `LifecycleManager` 내부로 이동시키거나 `_phase_lifecycle` 단계에서 명시적으로 호출하여 Phase 4의 책임을 완결시킬 것.

### 3순위: Household Facade 경량화
*   **현상**: `Household` 클래스가 컴포넌트들의 State DTO에 대한 수많은 Wrapper Property를 가지고 있어 유지보수 비용이 높음.
*   **제안**: 외부(Manager 등)에서 `household.assets` 대신 `household.econ_state.assets`와 같이 컴포넌트 상태에 더 명시적으로 접근하도록 하거나, DTO 매핑 로직을 별도 Mapper 클래스로 분리.
