from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from simulation.core_markets import Market

# DecisionEngine 인터페이스만 남기고, 구체적인 구현체는 decisions/ 하위 모듈로 분리합니다.


class DecisionEngine(ABC):
    """주체들의 의사결정 로직을 담는 추상 클래스"""

    @abstractmethod
    def make_decisions(
        self,
        agent: Any,
        markets: Dict[str, Market],
        goods_data: List[Dict[str, Any]],
        market_data: Dict[str, Any],
        current_time: int,
    ) -> List[Any]:
        raise NotImplementedError
