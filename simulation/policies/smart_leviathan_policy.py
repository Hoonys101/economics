from typing import Dict, Any
from simulation.interfaces.policy_interface import IGovernmentPolicy
import logging

logger = logging.getLogger(__name__)

class SmartLeviathanPolicy(IGovernmentPolicy):
    """
    WO-057: 적응형 AI 브레인 정책 엔진.
    Q-Learning 기반으로 실제 금리와 세율을 조절합니다.
    """
    
    def __init__(self, government: Any, config_module: Any):
        self.config = config_module
        # GovernmentAI는 이미 기존에 존재하거나 Jules Alpha가 구현할 클래스
        # 여기서는 인터페이스를 통해 연동
        from simulation.ai.government_ai import GovernmentAI
        self.ai = GovernmentAI(government, config_module)
        self.last_action_tick = -999

    def decide(self, government: Any, market_data: Dict[str, Any], current_tick: int) -> Dict[str, Any]:
        action_interval = getattr(self.config, "GOV_ACTION_INTERVAL", 30)
        
        # 30틱 주기로만 의사결정 수행
        if current_tick - self.last_action_tick < action_interval:
            return {"policy_type": "AI_ADAPTIVE", "status": "COOLDOWN"}

        # 1. AI에게 결정 위임
        action = self.ai.decide_policy(market_data, current_tick)
        self.last_action_tick = current_tick

        # 2. 결과 가공 (Action Index -> Policy Deltas)
        # Spec에 정의된 5-Action Mapping
        # 0: Dovish (-0.25%p)
        # 1: Hold
        # 2: Hawkish (+0.25%p)
        # 3: Expansion (-1.0%p Tax)
        # 4: Contraction (+1.0%p Tax)

        deltas = {"interest_rate_delta": 0.0, "tax_rate_delta": 0.0}
        label = "Hold"
        
        if action == 0: # Dovish
            deltas["interest_rate_delta"] = -0.0025
            label = "Dovish"
        elif action == 1: # Hold
            label = "Hold"
        elif action == 2: # Hawkish
            deltas["interest_rate_delta"] = 0.0025
            label = "Hawkish"
        elif action == 3: # Expansion
            deltas["tax_rate_delta"] = -0.01
            label = "Expansion"
        elif action == 4: # Contraction
            deltas["tax_rate_delta"] = 0.01
            label = "Contraction"
            
        # 3. 학습 업데이트
        # perceived_public_opinion 등을 reward로 사용하도록 유도
        reward = self._calculate_reward(government, market_data)
        self.ai.update_learning_with_state(reward, market_data)

        return {
            "interest_rate_delta": deltas["interest_rate_delta"],
            "tax_rate_delta": deltas["tax_rate_delta"],
            "policy_type": "AI_ADAPTIVE",
            "action_taken": action,
            "action_label": label
        }

    def _calculate_reward(self, government: Any, market_data: Dict[str, Any]) -> float:
        # Spec의 보상 함수 구현: - ( w1*(Inf_Gap^2) + w2*(Unemp_Gap^2) )
        # 구체적인 로직은 Jules Alpha가 채우겠지만, 인터페이스 레이어에서 가이드
        return getattr(government, "perceived_public_opinion", 0.5) 
