from abc import ABC, abstractmethod
from typing import Dict, Any


class IGovernmentPolicy(ABC):
    """
    정부 정책 결정을 위한 인터페이스.
    추후 테일러 준칙(Rule-based)과 AI(Adaptive) 정책을 교체할 수 있게 합니다.
    """

    @abstractmethod
    def decide(
        self, government: Any, market_data: Dict[str, Any], current_tick: int
    ) -> Dict[str, Any]:
        """
        경제 상황을 분석하여 정책(금리, 세율, 예산 배분 등)을 결정합니다.

        Returns:
            Dict[str, Any]: 결정된 정책 변수들 (e.g., {"base_rate": 0.05, "income_tax": 0.1, ...})
        """
        pass
