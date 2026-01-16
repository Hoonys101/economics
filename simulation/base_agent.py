from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging


class BaseAgent(ABC):
    def __init__(
        self,
        id: int,
        initial_assets: float,
        initial_needs: Dict[str, float],
        decision_engine: Any,
        value_orientation: str,
        name: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.id = id
        self.assets = initial_assets
        self.needs = initial_needs
        self.decision_engine = decision_engine
        self.value_orientation = value_orientation
        self.name = name if name is not None else f"{self.__class__.__name__}_{id}"
        self.inventory: Dict[str, float] = {}
        self.is_active: bool = True
        self.logger = logger if logger is not None else logging.getLogger(self.name)
        self._pre_state_data: Dict[str, Any] = {}  # 이전 상태 저장을 위한 속성
        self.pre_state_snapshot: Dict[str, Any] = {} # Mypy fix: Snapshot for learning
        self.generation: int = 0
        
        # [Cleanup] Standardized Memory Structure
        self.memory: Dict[str, Any] = {}

    def get_agent_data(self) -> Dict[str, Any]:
        """AI 의사결정에 필요한 에이전트의 현재 상태 데이터를 반환합니다."""
        # 이 메서드는 하위 클래스에서 구체적인 내용을 구현해야 합니다.
        raise NotImplementedError

    def get_pre_state_data(self) -> Dict[str, Any]:
        """이전 틱의 에이전트 상태 데이터를 반환합니다."""
        return self._pre_state_data

    def update_pre_state_data(self):
        """현재 상태 데이터를 다음 틱을 위해 이전 상태 데이터로 저장합니다."""
        self._pre_state_data = self.get_agent_data()

    @abstractmethod
    def update_needs(self, current_tick: int):
        pass

    @abstractmethod
    def make_decision(self, markets: Dict[str, Any], goods_data: list[Dict[str, Any]], market_data: Dict[str, Any], current_time: int) -> tuple[list[Any], Any]:
        pass

    @abstractmethod
    def clone(self, new_id: int, initial_assets_from_parent: float, current_tick: int) -> "BaseAgent":
        """
        현재 에이전트 인스턴스를 복제하여 새로운 에이전트를 생성합니다.
        AI 모델(decision_engine)을 포함하여 깊은 복사를 수행합니다.
        initial_assets_from_parent: 복제될 에이전트가 부모 에이전트로부터 물려받을 초기 자산.
        """
        pass
