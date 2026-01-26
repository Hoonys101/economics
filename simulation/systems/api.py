"""
God Class 리팩토링을 위한 새로운 시스템 및 컴포넌트의 계약을 정의합니다.

이 파일은 새로운 아키텍처 요소의 공개 API를 설정하여 명확한 경계와 타입 안전성을 보장합니다.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Protocol, TypedDict, Deque, Tuple
from abc import ABC, abstractmethod

# 순환 참조를 피하기 위한 Forward declarations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.firms import Firm
    from simulation.agents.government import Government
    from simulation.config import SimulationConfig
    from simulation.systems.reflux_system import EconomicRefluxSystem
    from simulation.ai.vectorized_planner import VectorizedHouseholdPlanner
    from simulation.metrics.economic_tracker import EconomicIndicatorTracker
    from simulation.dtos import GovernmentStateDTO, LeisureEffectDTO
    from simulation.markets.market import Market
    from simulation.dtos.scenario import StressScenarioConfig
    from simulation.dtos.api import SimulationState
    from simulation.models import Transaction


# ===================================================================
# 1. 시스템 간 통신을 위한 DTO (Data Transfer Objects)
# ===================================================================

class SocialMobilityContext(TypedDict):
    """사회적 이동성 계산에 필요한 데이터입니다."""
    households: List['Household']
    # housing_manager: Any # API 단순화를 위해 Any, 실제로는 HousingManager 인스턴스

class EventContext(TypedDict):
    """이벤트 처리에 필요한 데이터입니다."""
    households: List['Household']
    firms: List['Firm']
    markets: Dict[str, 'Market']
    government: Optional['Government']
    central_bank: Optional['Any'] # CentralBank
    bank: Optional['Any'] # Bank

class SensoryContext(TypedDict):
    """감각 시스템 처리에 필요한 데이터입니다."""
    tracker: 'EconomicIndicatorTracker'
    government: 'Government'
    time: int

class CommerceContext(TypedDict):
    """상거래 시스템이 소비를 실행하는 데 필요한 데이터입니다."""
    households: List['Household']
    agents: Dict[int, Any] # For O(1) lookup
    breeding_planner: 'VectorizedHouseholdPlanner'
    household_time_allocation: Dict[int, float]
    reflux_system: 'EconomicRefluxSystem'
    market_data: Dict[str, Any]
    config: Any
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

class SystemInterface(Protocol):
    """
    WO-103: Common interface for system services to enforce the sacred sequence.
    """
    def execute(self, state: SimulationState) -> None:
        ...

class ISocialSystem(Protocol):
    """사회적 순위 및 지위와 같은 동적 요소를 관리하는 시스템의 인터페이스입니다."""
    def __init__(self, config: Any): ...

    def update_social_ranks(self, context: SocialMobilityContext) -> None:
        """모든 가계의 사회적 순위 백분위를 계산하고 할당합니다."""
        ...

    def calculate_reference_standard(self, context: SocialMobilityContext) -> Dict[str, float]:
        """최상위 사회 계층의 평균 소비 및 주거 수준을 계산합니다."""
        ...


class IEventSystem(Protocol):
    """예약되거나 트리거된 시뮬레이션 전반의 이벤트를 관리하는 시스템의 인터페이스입니다."""
    def __init__(self, config: Any): ...

    def execute_scheduled_events(self, time: int, context: EventContext, config: StressScenarioConfig) -> None:
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

    def __init__(self, config: Any): ...

    def generate_government_sensory_dto(self, context: SensoryContext) -> 'GovernmentStateDTO':
        """주요 지표의 SMA를 계산하고 DTO로 패키징합니다."""
        ...


class ICommerceSystem(Protocol):
    """틱의 소비 및 여가 부분을 관리하는 시스템의 인터페이스입니다."""
    def __init__(self, config: Any, reflux_system: 'EconomicRefluxSystem'): ...

    def plan_consumption_and_leisure(self, context: CommerceContext, scenario_config: Optional[StressScenarioConfig] = None) -> Tuple[Dict[int, Dict[str, Any]], List[Transaction]]:
        """
        Phase 1: 소비 및 여가 계획. Fast Purchase를 위한 트랜잭션 생성.
        """
        ...

    def finalize_consumption_and_leisure(self, context: CommerceContext, planned_consumptions: Dict[int, Dict[str, Any]]) -> Dict[int, float]:
        """
        Phase 4: 소비 실행(재고 차감) 및 여가 효과 적용.
        """
        ...

# ===================================================================
# 3. 에이전트 컴포넌트 인터페이스 (Household 클래스에서 추출)
# ===================================================================

class IAgentLifecycleComponent(Protocol):
    """
    에이전트의 틱당 생명주기를 조율하는 컴포넌트 인터페이스입니다.
    혼란스러웠던 `update_needs` 메서드를 대체합니다.
    """
    def __init__(self, owner: 'Household', config: Any): ...

    def run_tick(self, context: LifecycleContext) -> None:
        """
        에이전트의 틱(일하기, 소비하기, 세금내기, 심리상태 업데이트)을 조율합니다.
        """
        ...


class IMarketComponent(Protocol):
    """판매자 선택과 같은 시장 상호작용을 책임지는 컴포넌트 인터페이스입니다."""
    def __init__(self, owner: 'Household', config: Any): ...

    def choose_best_seller(self, item_id: str, context: MarketInteractionContext) -> Tuple[Optional[int], float]:
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

    def __init__(self, config: Any): ...

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

class AgentLifecycleManagerInterface(SystemInterface, Protocol):
    """
    Interface for AgentLifecycleManager to ensure contract compliance.
    """
    pass
