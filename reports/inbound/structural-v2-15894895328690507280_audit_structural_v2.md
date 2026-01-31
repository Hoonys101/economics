# [AUDIT-STRUCTURAL-V2] 구조적 결함 및 누출된 추상화 전수 조사

**작성일:** 2024-10-24
**작성자:** Jules (AI Architect)
**대상:** Simulation Core (`simulation/`)

본 보고서는 `simulation/core_agents.py`의 God Class 위험도, 의사결정 엔진의 Leaky Abstraction, 그리고 `tick_scheduler.py`의 시퀀스 준수 여부를 정밀 분석한 결과입니다.

---

## 1. God Class 위험군 리스트 (비대화 및 복잡도)

800라인 이상의 파일 및 상속/책임이 과도한 클래스를 식별했습니다.

| 파일 경로 | 라인 수 | 주요 클래스 | 위험 요인 |
|---|---|---|---|
| `simulation/core_agents.py` | 900+ | `Household` | **Critical.** `BaseAgent` -> `ILearningAgent` 상속. `BioComponent`, `EconComponent`, `SocialComponent`로 위임하고 있으나 여전히 Facade가 거대함. `make_decision` 로직과 수많은 Property Proxy가 존재. |
| `simulation/tick_scheduler.py` | 777 | `TickScheduler` | **Warning.** 단일 Tick의 실행 흐름을 제어하나, 약 800라인에 육박하며 "System Transactions" 생성 로직이 비대함. |
| `simulation/db/repository.py` | 745 | `Repository` | **Warning.** 데이터베이스 접근 로직이 집중됨. |
| `simulation/firms.py` | 658 | `Firm` | **Warning.** `Household`와 유사하게 생산, 재무, 인사 등 모든 로직의 진입점 역할을 함. |

**분석:**
* `Household` 클래스는 컴포넌트 패턴(`self.econ_component` 등)을 도입했으나, 하위 호환성을 위한 Property Proxy 코드가 파일의 상당 부분을 차지하고 있음.
* `TickScheduler`는 단순한 스케줄러를 넘어, 시스템 레벨의 트랜잭션 생성(은행, 정부, 교육 등) 로직을 모두 포함하고 있어 응집도가 낮음.

---

## 2. Leaky Abstraction 위반 지점 (DTO 미사용)

의사결정(`make_decision`) 과정에서 Agent 인스턴스(`self`)나 `Government`, `Market` 엔티티가 DTO가 아닌 원본 객체 그대로 전달되는 지점입니다.

### A. DecisionContext 생성 및 전달 위반
`DecisionContext`는 순수 데이터(DTO)만 포함해야 하지만, 현재 라이브 객체 참조를 포함하고 있습니다.

* **위치:** `simulation/core_agents.py` (Household.make_decision)
* **코드:**
 ```python
 # Context for Decision Engine (Pure Logic) - BUT contains leaky objects
 context = DecisionContext(
 state=state_dto,
 config=config_dto,
 markets=markets, # VIOLATION: Dictionary of Market Objects (Entities)
 goods_data=goods_data,
 market_data=market_data,
 current_time=current_time,
 government=government, # VIOLATION: Government Agent Object (Entity)
 stress_scenario_config=stress_scenario_config
 )
 ```

### B. make_decision 호출부 위반
`TickScheduler`에서 에이전트의 의사결정 메서드를 호출할 때, `WorldState`의 라이브 객체들을 직접 주입하고 있습니다.

* **위치:** `simulation/tick_scheduler.py` (`_phase_decisions` 메서드)
* **위반 코드:**
 ```python
 firm_orders, action_vector = firm.make_decision(
 state.markets, # Live Object
 state.goods_data,
 market_data,
 state.time,
 state.government, # Live Object
 state.reflux_system, # Live Object
 stress_config
 )
 ```
 ```python
 household_orders, action_vector = household.make_decision(
 state.markets, # Live Object
 state.goods_data,
 market_data,
 state.time,
 state.government, # Live Object
 macro_context,
 stress_config
 )
 ```

### C. 인터페이스 정의 위반
* `simulation/core_agents.py`: `def make_decision(..., government: Optional[Any] = None, ...)` -> `government` 타입을 명시하지 않고 `Any`로 받거나 객체를 직접 받음.
* `simulation/decisions/base_decision_engine.py`: `context` 객체 내부에 라이브 객체 참조 허용.

---

## 3. Sequence Check (시퀀스 준수 여부)

**명세 기준:** Decisions -> Matching -> Transactions -> Lifecycle (The Sacred Sequence)

**`simulation/tick_scheduler.py` 분석 결과:**

1. **Main Sequence 준수:** `run_tick` 메서드 하단에 "THE SACRED SEQUENCE ()" 주석과 함께 4단계가 명시적으로 구현되어 있음.
 * `_phase_decisions`
 * `_phase_matching`
 * `_phase_transactions`
 * `_phase_lifecycle`

2. **구조적 우회 및 예외 (Deviation):**
 * **Pre-Sequence (System Transactions):** Main Sequence 이전에 방대한 "시스템 트랜잭션" 생성 단계가 존재함.
 * Firm Production, Bank Tick, Debt Service, Welfare, Infrastructure, Education.
 * 이들은 `system_transactions` 리스트에 담겨 `_phase_transactions`로 전달되므로, 트랜잭션 처리 *시점*은 준수하나, "Decision" 단계가 분산되어 있음(에이전트 결정 전 시스템이 강제 결정).
 * **Post-Tick Bypass (Commerce System):**
 * `state.commerce_system.execute_consumption_and_leisure`가 **Lifecycle 이후(Post-Tick)**에 실행됨.
 * **위험:** 소비(Consumption)는 자원과 돈을 사용하는 행위이므로 `Decisions -> Transactions` 흐름에 있어야 함. 현재는 Post-Tick에서 처리되어, 에이전트가 다음 틱이 될 때까지 잔고 감소나 재고 소모를 "Transaction Processor"를 통해 원장 검증 없이 수행할 가능성이 있음. (직접 상태 변경 위험).

---

## 4. 아키텍처 부채 상환 우선순위 제안

1. **[High] DecisionContext Purity (Leaky Abstraction 해결)**
 * `DecisionContext`에서 `markets` (객체)와 `government` (객체)를 제거.
 * 대신 필요한 정보(가격, 세율, 정책 등)만 담은 `MarketSnapshotDTO`와 `GovernmentPolicyDTO`를 생성하여 주입.
 * `Household.make_decision` 및 `Firm.make_decision` 시그니처 변경.

2. **[Medium] Post-Tick Consumption Integration**
 * `commerce_system.execute_consumption_and_leisure`를 "Decisions" 단계(가구의 소비 결정)와 "Transactions" 단계(실제 차감)로 분리하여 Main Sequence 안으로 편입.

3. **[Medium] Household Class Decomposition**
 * `simulation/core_agents.py`의 `Household` 클래스에서 Property Proxy들을 제거하고, 외부에서 `household.econ.assets` 처럼 컴포넌트에 직접 접근하거나, 명확한 Facade 인터페이스만 남기도록 리팩토링.

4. **[Low] TickScheduler Logic Extraction**
 * Pre-Sequence의 시스템 트랜잭션 생성 로직(Bank, Welfare 등)을 별도의 `SystemTransactionGenerator` 서비스로 분리하여 `TickScheduler`의 라인 수를 줄이고 역할을 스케줄링으로 한정.