from _typeshed import Incomplete
from simulation.ai.enums import Personality as Personality
from simulation.ai.firm_ai import FirmAI as FirmAI
from simulation.firms import Firm as Firm

logger: Incomplete

class ServiceFirmAI(FirmAI):
    """
    서비스 기업용 AI 엔진 (Phase 17-1).
    재고 기반 상태 대신 가동률(Utilization Rate) 기반 상태를 사용.
    """
    def calculate_reward(self, firm_agent: Firm, prev_state: dict, current_state: dict) -> float:
        """
        Add Waste Penalty to standard reward.
        """
