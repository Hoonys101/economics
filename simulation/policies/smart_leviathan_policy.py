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

        # Enforce 30-tick (1 month) silent interval
        if current_tick % action_interval != 0:
            return {"policy_type": "AI_ADAPTIVE", "status": "HOLD_INTERVAL"}

        # 1. AI Brain makes a decision
        action_idx = self.ai.decide_policy(market_data, current_tick)

        # Get current policy values
        central_bank = market_data["central_bank"]
        old_rate = central_bank.base_rate
        old_tax = government.tax_rate
        old_budget = government.budget_allocation

        new_rate = old_rate
        new_tax = old_tax
        new_budget = old_budget

        # 2. Translate Action Index to Policy Delta (Baby Step principle)
        if action_idx == 0:  # Dovish
            new_rate -= 0.0025
        elif action_idx == 1:  # Neutral
            pass # No change
        elif action_idx == 2:  # Hawkish
            new_rate += 0.0025
        elif action_idx == 3:  # Fiscal Ease
            new_tax -= 0.01
        elif action_idx == 4:  # Fiscal Tight
            new_tax += 0.01
            new_budget -= 0.05

        # 3. Enforce STRICT CLAMPING (Safety Valve)
        clamped_rate = max(0.0, min(0.20, new_rate))
        clamped_tax = max(0.05, min(0.50, new_tax))
        clamped_budget = max(0.1, min(1.0, new_budget))

        # 4. Log every change
        if old_rate != clamped_rate:
            logger.info(f"BABY_STEP | Rate: {old_rate:.4f} -> {clamped_rate:.4f}", extra={"tick": current_tick})
        if old_tax != clamped_tax:
            logger.info(f"BABY_STEP | Tax: {old_tax:.4f} -> {clamped_tax:.4f}", extra={"tick": current_tick})
        if old_budget != clamped_budget:
            logger.info(f"BABY_STEP | Budget: {old_budget:.4f} -> {clamped_budget:.4f}", extra={"tick": current_tick})

        # 5. Update System State
        central_bank.base_rate = clamped_rate
        government.tax_rate = clamped_tax
        government.budget_allocation = clamped_budget

        # 6. Trigger AI Learning Update
        reward = self._calculate_reward(government, market_data)
        self.ai.update_learning_with_state(reward, market_data)

        return {
            "policy_type": "AI_ADAPTIVE",
            "status": "ACTION_TAKEN",
            "action": action_idx,
            "base_rate": clamped_rate,
            "tax_rate": clamped_tax,
            "budget_allocation": clamped_budget,
        }

    def _calculate_reward(self, government: Any, market_data: Dict[str, Any]) -> float:
        # Spec의 보상 함수 구현: - ( w1*(Inf_Gap^2) + w2*(Unemp_Gap^2) )
        # 구체적인 로직은 Jules Alpha가 채우겠지만, 인터페이스 레이어에서 가이드
        return getattr(government, "perceived_public_opinion", 0.5) 
