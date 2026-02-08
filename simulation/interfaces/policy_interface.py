from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.dtos.policy_dtos import PolicyContextDTO, PolicyDecisionResultDTO

class IGovernmentPolicy(ABC):
    """
    정부 정책 결정을 위한 인터페이스.
    추후 테일러 준칙(Rule-based)과 AI(Adaptive) 정책을 교체할 수 있게 합니다.
    """
    
    @abstractmethod
    def decide(self, context: "PolicyContextDTO") -> "PolicyDecisionResultDTO":
        """
        경제 상황을 분석하여 정책(금리, 세율, 예산 배분 등)을 결정합니다.
        
        Args:
            context (PolicyContextDTO): 정책 결정을 위한 읽기 전용 컨텍스트.

        Returns:
            PolicyDecisionResultDTO: 결정된 정책 및 상태 업데이트.
        """
        pass
