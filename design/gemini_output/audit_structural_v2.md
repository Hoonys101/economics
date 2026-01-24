# [AUDIT-STRUCTURAL-V2] 구조적 결함 및 누출된 추상화 전수 조사 보고서

## 1. God Class 위험군 리스트

코드베이스 스캔 결과, 다음과 같은 파일들이 'God Class' 위험군(800라인 근접 또는 초과)으로 식별되었습니다. 또한 상속 계층이 깊은 클래스들도 확인되었습니다.

### A. 파일 크기 기준 (Critical > 800 lines)
| 파일 경로 | 라인 수 | 위험도 | 설명 |
|---|---|---|---|
| `simulation/core_agents.py` | 900+ | **CRITICAL** | `Household` 클래스가 정의된 파일로, 생물학적/경제적/사회적 로직이 혼재되어 있어 비대화가 심각함. |
| `simulation/db/repository.py` | 745 | WARNING | 데이터베이스 접근 로직이 집중되어 있어 향후 병목이 될 가능성 높음. |
| `simulation/tick_scheduler.py` | 738 | WARNING | 시뮬레이션의 모든 단계(Phase) 로직이 절차적으로 나열되어 있어 유지보수가 어려워질 수 있음. |

### B. 상속 계층 깊이 기준 (Depth >= 4)
| 클래스명 | 깊이 | 상속 구조 (추정) |
|---|---|---|
| `ServiceFirm` | 4 | BaseAgent -> Firm -> ServiceFirm (Note: BaseAgent inherits from something else or mixins involved) |
| `ServiceFirmAI` | 4 | ServiceFirm와 유사 구조 |
| `AgentLifecycleManager` | 4 | BaseSystem -> LifecycleManager -> ... |

---

## 2. Leaky Abstraction (DTO 미사용) 위반 지점

의사결정 엔진(`DecisionEngine`)에 에이전트의 원시 객체(`self`, `Government`, `RefluxSystem`)를 직접 전달하여 캡슐화를 위반하는 지점들이 발견되었습니다.

### A. DecisionContext 생성 시 Raw Object 주입
`DecisionContext`는 순수한 데이터 객체(DTO)들로만 구성되어야 하나, 아래 코드에서는 활성 에이전트 객체를 직접 참조하고 있습니다.

1.  **`simulation/firms.py` (Firm.make_decision)**
    ```python
    context = DecisionContext(
        state=state_dto,
        config=config_dto,
        markets=markets,             # [VIOLATION] Raw Market Objects
        goods_data=goods_data,
        market_data=market_data,
        current_time=current_time,
        government=government,       # [VIOLATION] Raw Government Agent Object
        reflux_system=reflux_system, # [VIOLATION] Raw System Object
        stress_scenario_config=stress_scenario_config,
    )
    ```

2.  **`simulation/core_agents.py` (Household.make_decision)**
    ```python
    context = DecisionContext(
        state=state_dto,
        config=config_dto,
        markets=markets,             # [VIOLATION] Raw Market Objects
        goods_data=goods_data,
        market_data=market_data,
        current_time=current_time,
        government=government,       # [VIOLATION] Raw Government Agent Object
        stress_scenario_config=stress_scenario_config
    )
    ```

### B. TickScheduler에서의 주입 지점
`TickScheduler`가 에이전트의 `make_decision` 메서드를 호출할 때 원시 시스템 객체를 주입하고 있습니다.

*   **`simulation/tick_scheduler.py`**:
    *   `firm.make_decision(..., state.government, state.reflux_system, ...)`
    *   `household.make_decision(..., state.government, ...)`

---

## 3. TickScheduler 시퀀스 준수 여부 (Sequence Check)

명세된 `Decisions -> Matching -> Transactions -> Lifecycle` 순서와 비교하여 다음과 같은 구조적 이탈이 확인되었습니다.

### A. 주요 시퀀스 흐름
`TickScheduler.run_tick` 메서드는 명목상 아래 순서를 따르고 있습니다:
1.  `_phase_decisions` (Decisions)
2.  `_phase_matching` (Matching)
3.  `_phase_transactions` (Transactions)
4.  `_phase_lifecycle` (Lifecycle)

### B. 구조적 이탈 및 우회 (Bypasses)
그러나 위 메인 페이즈 **이전**과 **이후**에 중요한 경제적 행위가 분산되어 발생하고 있습니다.

1.  **Transaction Generation Phase (Pre-Decisions)**
    *   `_phase_decisions` 이전에 `System Transactions`라는 이름으로 아래 행위들이 선행됨:
        *   `state.bank.run_tick`: 이자 발생 (금융 결정)
        *   `firm.generate_transactions`: 임금, 세금, 배당금 계산 (재무 결정)
        *   `state.government.run_welfare_check`: 복지 지급
        *   `state.finance_system.service_debt`: 부채 상환
    *   **문제점**: 에이전트들이 자신의 의사결정 페이즈(`Decisions`)에 들어가기도 전에 강제적인 재무 트랜잭션이 생성됨. 이는 "모든 결정은 Decision Phase에서 일어난다"는 원칙을 일부 약화시킴.

2.  **Post-Lifecycle Logic (Post-Tick)**
    *   `state.commerce_system.execute_consumption_and_leisure`: 가계의 소비 및 여가 활동이 `Lifecycle` 이후에 발생.
    *   `state.housing_system.process_housing`: 임대료 지불 및 주거 페널티 처리가 모든 페이즈가 끝난 뒤 별도로 실행됨.
    *   **문제점**: 소비와 주거 비용 지불은 경제 활동의 핵심이므로 `Decisions` (소비 결정) 및 `Matching` (시장 상호작용) 단계에 통합되어야 이상적임. 현재는 별도의 시스템 호출로 우회되어 있음.

---

## 4. 아키텍처 부채 상환 우선순위 제안

### Priority 1: Critical (즉시 해결 권장)
1.  **`DecisionContext` DTO화**: `government` 객체 전체를 넘기는 대신, 의사결정에 필요한 정보만 담은 `GovernmentPolicyDTO` 등을 생성하여 전달해야 함. `reflux_system` 또한 필요한 데이터만 추출하거나 `IFinanceSystem` 인터페이스를 통해 제한적으로 접근하도록 변경 필요.
2.  **`core_agents.py` 리팩토링**: 900라인이 넘는 `Household` 클래스를 `BioComponent`, `EconComponent`, `SocialComponent` 등으로 분리하였으나 여전히 퍼사드(Facade)가 비대함. 위임 코드를 정리하고 파일을 분리해야 함.

### Priority 2: Warning (다음 스프린트)
3.  **Consumption/Housing 로직의 페이즈 통합**: `CommerceSystem`과 `HousingSystem`의 로직을 `Decisions` (주문 생성) -> `Matching` (거래 체결) 흐름으로 편입시켜 시퀀스의 일관성을 확보.
4.  **`TickScheduler` 간소화**: `run_tick` 메서드의 절차적 로직을 `PhaseManager` 등으로 위임하거나, 이벤트 기반으로 변경하여 복잡도 관리.

### Priority 3: Refactoring (장기 과제)
5.  **상속 구조 개선**: `ServiceFirm` 등의 상속 깊이를 줄이기 위해 상속 대신 컴포지션(Composition) 패턴 활용 검토.
