Okay, I will now draft the 'Zero-Question Spec' for the "God Class" refactoring task (TD-043/044/045).

First, I will create the necessary directories and files for the new System and Component APIs.
팀장님, 지시하신 대로 'God Class' 리팩토링(TD-043/044/045)을 위한 '질문 제로(Zero-Question)' 수준의 상세 명세서(Spec) 초안을 작성했습니다.

먼저, 새로운 시스템과 컴포넌트의 인터페이스 계약을 담은 `api.py` 파일의 내용입니다.

```python
# 파일 경로: simulation/systems/api.py
"""
God Class 리팩토링을 위한 새로운 시스템 및 컴포넌트의 계약을 정의합니다.

이 파일은 새로운 아키텍처 요소의 공개 API를 설정하여 명확한 경계와 타입 안전성을 보장합니다.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Protocol, TypedDict, Deque
from abc import ABC, abstractmethod

# 순환 참조를 피하기 위한 Forward declarations
if 'TYPE_CHECKING':
    from simulation.core_agents import Household, Firm
    from simulation.agents.government import Government
    from simulation.config import SimulationConfig
    from simulation.systems.reflux_system import EconomicRefluxSystem
    from simulation.ai.vectorized_planner import VectorizedHouseholdPlanner
    from simulation.metrics.economic_tracker import EconomicIndicatorTracker
    from simulation.dtos import GovernmentStateDTO
    from simulation.markets.market import Market


# ===================================================================
# 1. 시스템 간 통신을 위한 DTO (Data Transfer Objects)
# ===================================================================

class SocialMobilityContext(TypedDict):
    """사회적 이동성 계산에 필요한 데이터입니다."""
    households: List['Household']
    housing_manager: Any # API 단순화를 위해 Any, 실제로는 HousingManager 인스턴스

class EventContext(TypedDict):
    """이벤트 처리에 필요한 데이터입니다."""
    households: List['Household']
    firms: List['Firm']
    markets: Dict[str, 'Market']

class SensoryContext(TypedDict):
    """감각 시스템 처리에 필요한 데이터입니다."""
    tracker: 'EconomicIndicatorTracker'
    government: 'Government'
    time: int

class CommerceContext(TypedDict):
    """상거래 시스템이 소비를 실행하는 데 필요한 데이터입니다."""
    households: List['Household']
    breeding_planner: 'VectorizedHouseholdPlanner'
    household_time_allocation: Dict[int, float]
    reflux_system: 'EconomicRefluxSystem'
    market_data: Dict[str, Any]
    config: 'SimulationConfig'
    time: int

class LifecycleContext(TypedDict):
    """에이전트 생명주기 관리에 필요한 데이터입니다."""
    household: 'Household' # 개별 가계를 대상으로 실행
    market_data: Dict[str, Any]
    time: int

class MarketInteractionContext(TypedDict):
    """시장 상호작용 컴포넌트에 필요한 데이터입니다."""
    markets: Dict[str, 'Market']

class LearningUpdateContext(TypedDict):
    """에이전트의 AI 학습 업데이트에 필요한 데이터입니다."""
    reward: float
    next_agent_data: Dict[str, Any]
    next_market_data: Dict[str, Any]

# ===================================================================
# 2. 시스템 레벨 인터페이스 (Simulation 클래스에서 추출)
# ===================================================================

class ISocialSystem(Protocol):
    """사회적 순위 및 지위와 같은 동적 요소를 관리하는 시스템의 인터페이스입니다."""
    def __init__(self, config: 'SimulationConfig'): ...

    def update_social_ranks(self, context: SocialMobilityContext) -> None:
        """모든 가계의 사회적 순위 백분위를 계산하고 할당합니다."""
        ...

    def calculate_reference_standard(self, context: SocialMobilityContext) -> Dict[str, float]:
        """최상위 사회 계층의 평균 소비 및 주거 수준을 계산합니다."""
        ...


class IEventSystem(Protocol):
    """예약되거나 트리거된 시뮬레이션 전반의 이벤트를 관리하는 시스템의 인터페이스입니다."""
    def __init__(self, config: 'SimulationConfig'): ...

    def execute_scheduled_events(self, time: int, context: EventContext) -> None:
        """현재 틱에 예약된 카오스 이벤트나 다른 시나리오를 실행합니다."""
        ...


class ISensorySystem(Protocol):
    """
    원시 데이터를 정부 AI와 같은 에이전트의 의사결정을 위해 평활화되거나 집계된 지표로
    처리하는 시스템의 인터페이스입니다.
    """
    # 상태(State)는 반드시 이 시스템으로 이전되어야 합니다.
    inflation_buffer: Deque[float]
    unemployment_buffer: Deque[float]
    gdp_growth_buffer: Deque[float]
    wage_buffer: Deque[float]
    approval_buffer: Deque[float]
    last_avg_price_for_sma: float
    last_gdp_for_sma: float

    def __init__(self, config: 'SimulationConfig'): ...

    def generate_government_sensory_dto(self, context: SensoryContext) -> 'GovernmentStateDTO':
        """주요 지표의 SMA를 계산하고 DTO로 패키징합니다."""
        ...


class ICommerceSystem(Protocol):
    """틱의 소비 및 여가 부분을 관리하는 시스템의 인터페이스입니다."""
    def __init__(self, config: 'SimulationConfig', reflux_system: 'EconomicRefluxSystem'): ...

    def execute_consumption_and_leisure(self, context: CommerceContext) -> None:
        """가계 소비, 긴급 구매(fast-track purchases), 여가 효과를 조율합니다."""
        ...

# ===================================================================
# 3. 에이전트 컴포넌트 인터페이스 (Household 클래스에서 추출)
# ===================================================================

class IAgentLifecycleComponent(Protocol):
    """
    에이전트의 틱당 생명주기를 조율하는 컴포넌트 인터페이스입니다.
    혼란스러웠던 `update_needs` 메서드를 대체합니다.
    """
    def __init__(self, owner: 'Household', config: 'SimulationConfig'): ...

    def run_tick(self, context: LifecycleContext) -> None:
        """
        에이전트의 틱(일하기, 소비하기, 세금내기, 심리상태 업데이트)을 조율합니다.
        """
        ...


class IMarketComponent(Protocol):
    """판매자 선택과 같은 시장 상호작용을 책임지는 컴포넌트 인터페이스입니다."""
    def __init__(self, owner: 'Household', config: 'SimulationConfig'): ...

    def choose_best_seller(self, item_id: str, context: MarketInteractionContext) -> tuple[Optional[int], float]:
        """
        가격, 품질, 브랜드 인지도, 충성도를 포함하는 효용에 기반하여
        주어진 아이템에 대한 최적의 판매자를 선택합니다.
        """
        ...

class ILaborMarketAnalyzer(Protocol):
    """
    노동 시장의 시스템 레벨 분석기 인터페이스입니다.
    이 로직은 개별 에이전트에 속하지 않습니다.
    """
    market_wage_history: Deque[float]

    def __init__(self, config: 'SimulationConfig'): ...

    def calculate_shadow_reservation_wage(self, agent: 'Household', market_data: Dict[str, Any]) -> float:
        """가계의 고정적인 유보 임금을 계산합니다."""
        ...

    def update_market_history(self, market_data: Dict[str, Any]) -> None:
        """최신 시장 전체 임금 데이터로 내부 기록을 업데이트합니다."""
        ...


# ===================================================================
# 4. 에이전트 학습 계약 (Firm 및 Household용)
# ===================================================================

class ILearningAgent(Protocol):
    """Firm 및 Household와 같은 에이전트의 공통 메서드를 나타내는 프로토콜입니다."""
    id: int
    is_active: bool

    def update_learning(self, context: LearningUpdateContext) -> None:
        """
        시뮬레이션 엔진이 에이전트의 내부 AI 학습 프로세스를 트리거하기 위한
        단일의 고수준 메서드입니다. 에이전트는 이 요청을 내부 컴포넌트(예: ai_engine)에
        위임할 책임이 있습니다.

        이는 "묻지 말고 시켜라(Tell, Don't Ask)" 원칙을 강제합니다.
        """
        ...
```

다음은 리팩토링의 상세 계획, 위험 관리, 검증 계획을 담은 Spec 문서입니다.

```markdown
# 상세 명세서: God Class 리팩토링 (TD-043/044/045)

## 1. 개요

- **목표**: `Simulation` 클래스와 `Household` 클래스의 단일 책임 원칙(SoC) 위반을 해결하여 시스템의 유지보수성, 테스트 용이성, 확장성을 개선합니다.
- **범위**:
    - `Simulation.run_tick`의 핵심 로직들을 `SocialSystem`, `EventSystem`, `SensorySystem`, `CommerceSystem`으로 분리합니다.
    - `Household`의 내부 로직을 `AgentLifecycleComponent`, `MarketComponent`와 같은 컴포넌트로 분리합니다.
    - `LaborMarketAnalyzer`를 도입하여 거시 경제 분석 로직을 중앙화합니다.
    - `Firm` 및 `Household`에 `update_learning` 계약을 도입하여 AI 학습 로직을 캡슐화합니다.

## 2. 아키텍처 원칙 및 위험 관리 (Audit Report 기반)

이 리팩토링은 다음 제약 조건을 엄격히 준수하여 감사 보고서에서 식별된 위험을 완화합니다.

- **[C-1] 시간적 결합성 보존**: 새로운 시스템은 **상태 비저장(stateless)** 프로세서로 설계됩니다. `run_tick`은 `God-Method`에서 각 시스템의 `execute` 메서드를 정해진 순서대로 호출하는 **`God-Orchestrator`**로 전환됩니다.
- **[C-2] 상태 소유권 이전**: 로직이 추출될 때 **관련 상태도 함께 이전**됩니다. 예를 들어, `inflation_buffer`와 같은 SMA 관련 상태는 `Simulation`에서 `SensorySystem`으로 완전히 이전됩니다.
- **[C-3] 신규 God 의존성 방지**: 새로운 시스템은 `__init__` 시점에 최소한의 필수 의존성(config, 다른 시스템 등)만 주입받습니다. **상위 `simulation` 객체를 하위 시스템에 전달하는 것은 금지됩니다.**
- **[C-4] 테스트 마이그레이션**: 각 신규 시스템에 대한 단위 테스트(`test_<system_name>.py`) 작성이 필수입니다. 기존 통합 테스트는 새로운 오케스트레이션 흐름을 검증하도록 리팩토링되어야 합니다.
- **[C-5] 컴포넌트 소유권**: `Household`에서 추출된 컴포넌트는 `owner` 참조를 통해 부모 에이전트의 상태를 읽습니다. (예: `MarketComponent(owner=self)`)
- **[C-6] 단방향 학습 업데이트**: `Simulation` 엔진은 `firm.update_learning(context)`만 호출합니다. 세부 학습 로직은 `Firm` 클래스 내부에 완전히 캡슐화됩니다.

## 3. API 명세 및 책임 (simulation.systems.api.py 참조)

### 3.1. 신규 시스템 (From `Simulation`)

#### **`SocialSystem`**
- **책임**: 사회적 순위 계산 및 준거 집단(reference standard) 분석.
- **상태 캡슐화**: 없음 (순수 프로세서).
- **`__init__(self, config)`**
- **`update_social_ranks(self, context: SocialMobilityContext)`**:
    - `context.households`를 순회하며 사회적 점수(소비, 주거 등)를 계산.
    - 정렬 후 백분위 순위를 `household.social_rank`에 업데이트.
- **`calculate_reference_standard(self, context: SocialMobilityContext)`**:
    - 상위 20% 가계 그룹을 식별.
    - 해당 그룹의 평균 소비와 주거 등급을 계산하여 반환.

#### **`EventSystem`**
- **책임**: 하드코딩된 시간 기반 이벤트(인플레이션 쇼크 등) 관리.
- **상태 캡슐화**: 없음 (순수 프로세서).
- **`__init__(self, config)`**
- **`execute_scheduled_events(self, time: int, context: EventContext)`**:
    - `time`을 기준으로 예정된 이벤트(예: `if time == 200: ...`)를 확인.
    - `context`의 `markets`, `households` 상태를 직접 수정하여 쇼크 적용.

#### **`SensorySystem`**
- **책임**: 정부 AI를 위한 거시 경제 지표 가공 및 평활화.
- **상태 캡슐화**: `inflation_buffer`, `unemployment_buffer`, `gdp_growth_buffer`, `wage_buffer`, `approval_buffer`, `last_avg_price_for_sma`, `last_gdp_for_sma`.
- **`__init__(self, config)`**: 내부 버퍼들을 초기화.
- **`generate_government_sensory_dto(self, context: SensoryContext)`**:
    - `context.tracker`에서 최신 원시 지표를 가져옴.
    - 인플레이션, 실업률, GDP 성장률 등을 계산하여 내부 버퍼에 추가.
    - 버퍼의 이동평균(SMA)을 계산.
    - 최종 결과를 `GovernmentStateDTO`로 패키징하여 반환.

#### **`CommerceSystem`**
- **책임**: 소비, 긴급 구매(fast purchase), 여가 효과 적용을 포함한 상거래 로직 총괄.
- **상태 캡슐화**: 없음 (순수 프로세서).
- **`__init__(self, config, reflux_system)`**
- **`execute_consumption_and_leisure(self, context: CommerceContext)`**:
    - `context.breeding_planner`를 호출하여 가계별 소비/구매 결정을 일괄 계산.
    - `context.households`를 순회하며 다음을 적용:
        1.  벡터화된 결과에 따라 `household.consume()` 호출.
        2.  긴급 구매(buy_list)가 있는 경우, `household.assets` 차감 및 `reflux_system`으로 자금 이전.
        3.  `context.household_time_allocation`을 참조하여 `household.apply_leisure_effect()` 호출.
        4.  (중요) `household.update_needs()`를 호출하여 생명주기 업데이트. 이 메서드는 `AgentLifecycleComponent.run_tick()`으로 리팩토링될 것임.

### 3.2. 신규 컴포넌트 및 분석기 (From `Household`)

#### **`MarketComponent` (Household 소유)**
- **책임**: 시장 상호작용, 특히 최적 판매자 선택 로직.
- **`__init__(self, owner: Household, config)`**
- **`choose_best_seller(self, item_id, context)`**:
    - `context.markets`에서 `item_id`에 대한 모든 판매자(ask) 정보를 조회.
    - `owner`의 `quality_preference`, `brand_loyalty`와 판매자의 `price`, `perceived_quality`, `brand_awareness`를 결합하여 효용(Utility) 점수 계산.
    - 최고 효용 점수를 가진 판매자 ID와 가격을 반환.

#### **`AgentLifecycleComponent` (Household 소유)**
- **책임**: `Household.update_needs`의 복잡한 오케스트레이션 로직을 대체.
- **`__init__(self, owner: Household, config)`**
- **`run_tick(self, context: LifecycleContext)`**:
    - **(기존 `update_needs` 로직 이전)**
    1.  노동 수행 (Work).
    2.  소비 결정 및 실행.
    3.  세금 납부.
    4.  심리 상태 업데이트 (`psychology.update_needs`).

#### **`LaborMarketAnalyzer` (시스템 레벨)**
- **책임**: 개별 에이전트가 아닌, 시스템 전체의 노동 시장 분석.
- **상태 캡슐화**: `market_wage_history` (Deque).
- **`__init__(self, config)`**
- **`update_market_history(self, market_data)`**: `market_data`에서 평균 임금을 추출하여 내부 `market_wage_history`에 추가.
- **`calculate_shadow_reservation_wage(self, agent, market_data)`**: `agent`의 고용 상태와 내부 `market_wage_history`를 기반으로 유보 임금을 계산하여 반환.

### 3.3. 에이전트 계약

#### **`Firm.update_learning(self, context: LearningUpdateContext)`**
- **책임**: `Simulation` 엔진으로부터 학습 신호를 받아 내부 AI 엔진에 전파.
- **구현 Pseudo-code**:
  ```python
  # In class Firm:
  def update_learning(self, context: LearningUpdateContext):
      # 엔진은 더 이상 firm.decision_engine.ai_engine에 접근하지 않음
      if hasattr(self.decision_engine, 'ai_engine'):
          reward = self.decision_engine.ai_engine.calculate_reward(...)
          self.decision_engine.ai_engine.update_learning_v2(
              reward=reward,
              next_agent_data=context.next_agent_data,
              ...
          )
  ```
- **`Household`**도 동일한 `update_learning` 인터페이스를 구현해야 함.

## 4. 리팩토링된 `Simulation.run_tick` 오케스트레이션

`run_tick`은 다음과 같은 순서로 각 시스템을 호출하는 책임만 가집니다.

```python
# Pseudo-code for a refactored Simulation.run_tick
def run_tick(self):
    self.time += 1
    
    # 1. 이벤트 처리 (Event System)
    event_context = EventContext(...)
    self.event_system.execute_scheduled_events(self.time, event_context)

    # 2. 사회적 순위 업데이트 (Social System)
    social_context = SocialMobilityContext(...)
    self.social_system.update_social_ranks(social_context)
    ref_std = self.social_system.calculate_reference_standard(social_context)
    market_data['reference_standard'] = ref_std

    # 3. 데이터 감지 및 가공 (Sensory System)
    sensory_context = SensoryContext(...)
    gov_dto = self.sensory_system.generate_government_sensory_dto(sensory_context)
    self.government.update_sensory_data(gov_dto)

    # ... (기존의 정부 정책 결정, 은행 이자 처리 등 순서 유지) ...

    # 4. 에이전트 의사결정 (기존 로직)
    # households.make_decision(), firms.make_decision() 호출
    # 이 과정에서 `household_time_allocation` 등 후속 시스템에 필요한 데이터가 생성됨

    # ... (시장 매칭 및 거래 처리 등 기존 로직) ...

    # 5. 소비 및 여가 활동 (Commerce System) - 중요: 거래 처리 이후에 실행
    commerce_context = CommerceContext(
        households=self.households,
        breeding_planner=self.breeding_planner,
        household_time_allocation=household_time_allocation, # 4번 단계에서 생성된 데이터
        ...
    )
    self.commerce_system.execute_consumption_and_leisure(commerce_context)
    
    # ... (기업 생산 및 법인세 징수 등 기존 로직) ...

    # 6. AI 학습 업데이트 (Agent Learning Contract)
    for agent in self.get_active_agents():
        learning_context = LearningUpdateContext(...)
        agent.update_learning(learning_context) # "Tell, Don't Ask"

    # ... (기타 정리 작업 및 상태 저장) ...
```

## 5. 검증 계획

1.  **단위 테스트**: `SocialSystem`, `EventSystem`, `SensorySystem`, `CommerceSystem`, `MarketComponent`, `LaborMarketAnalyzer` 각각에 대해 단위 테스트 파일을 생성합니다.
    - 예: `tests/systems/test_sensory_system.py`
    - 각 테스트는 시스템이 명세된 입력에 대해 정확한 출력을 생성하는지 검증합니다.
2.  **통합 테스트**: 기존의 `test_engine.py`를 리팩토링하여 `run_tick`의 새로운 오케스트레이션 흐름을 검증합니다.
    - 특정 틱 이후의 `government.sensory_data`가 예상과 일치하는지 확인.
    - 특정 틱 이후의 가계 `social_rank`가 예상과 일치하는지 확인.
3.  **Golden Sample 테스트**: 리팩토링 전/후의 `run_tick` 100회 실행 결과를 비교하여 주요 거시 지표(GDP, 실업률 등)의 변화가 허용 오차 범위 내에 있는지 확인합니다.

## 6. JULES 구현 지침

- **Routine**: 구현 중 발견되는 모든 기술 부채(예: "이 부분은 추가 리팩토링 필요")나 설계 개선 아이디어는 `communications/insights/` 폴더에 `[Insight] <주제>.md` 형식으로 기록 및 보고해야 합니다.
```
