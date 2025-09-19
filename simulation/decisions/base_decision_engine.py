from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any
import logging

if TYPE_CHECKING:
    from simulation.base_agent import BaseAgent
    from simulation.models import Order

logger = logging.getLogger(__name__)

class BaseDecisionEngine:
    """모든 의사결정 엔진의 기본 클래스"""
    def __init__(self) -> None:
        # 로거는 이제 모듈 레벨에서 관리됩니다.
        pass

    def make_decision(self, agent: BaseAgent, market_data: Dict[str, Any], current_tick: int) -> List[Order]:
        """에이전트의 의사결정을 내리고 주문 리스트를 반환합니다."""
        raise NotImplementedError

    def _allocate_budget(self, agent: BaseAgent) -> Dict[str, float]:
        """에이전트의 현재 자산과 욕구를 바탕으로 예산을 할당합니다."""
        # 기본적으로는 모든 자산을 소비 예산으로 할당
        return {"consumption_budget": agent.assets, "investment_budget": 0.0}