import logging
from _typeshed import Incomplete
from simulation.models import Order as Order
from typing import Any

class ActionProposalEngine:
    """
    에이전트의 상태에 기반하여 현실적인 후보 행동(주문) 목록을 생성합니다.
    '어떤 행동들을 할 수 있는가?'에 대한 책임을 집니다.
    """
    config_module: Incomplete
    n_action_samples: Incomplete
    logger: Incomplete
    def __init__(self, config_module: Any, n_action_samples: int = 10, logger: logging.Logger | None = None) -> None: ...
    def propose_actions(self, agent: Any, current_time: int) -> list[list[Order]]:
        """
        에이전트 유형에 따라 적절한 행동 제안 메서드를 호출합니다.
        """
    def propose_forced_labor_action(self, household: Any, current_time: int, wage_factor: float) -> Order:
        """
        강제 탐험을 위한 노동 판매 행동을 제안합니다.
        """
