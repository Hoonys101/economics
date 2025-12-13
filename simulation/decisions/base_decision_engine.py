from __future__ import annotations
from typing import List, Dict, Any, Tuple, TYPE_CHECKING
from simulation.models import Order

if TYPE_CHECKING:
    from simulation.core_markets import Market


class BaseDecisionEngine:
    def make_decisions(
        self,
        agent: Any,
        markets: Dict[str, "Market"],
        goods_data: List[Dict[str, Any]],
        market_data: Dict[str, Any],
        current_time: int,
    ) -> Tuple[List[Order], Any]:
        """
        에이전트의 현재 상태와 시장 정보를 바탕으로 의사결정을 내리고,
        그 결과로 생성된 주문 목록과 선택된 전술을 반환합니다.

        Args:
            agent: 의사결정을 내리는 주체 에이전트.
            markets: 접근 가능한 시장 객체 딕셔너리.
            goods_data: 시뮬레이션의 모든 재화 정보.
            market_data: 현재 틱의 요약된 시장 데이터.
            current_time: 현재 시뮬레이션 틱.

        Returns:
            (생성된 주문 목록, 선택된 전술) 튜플.
        """
        raise NotImplementedError
