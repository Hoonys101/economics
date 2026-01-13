from typing import Dict, Any, Deque
from collections import deque
from simulation.interfaces.policy_interface import IGovernmentPolicy
from simulation.utils.shadow_logger import log_shadow

class TaylorRulePolicy(IGovernmentPolicy):
    """
    WO-056: 테일러 준칙 기반의 정책 엔진.
    기존의 수식 기반 결정을 담당하며, 섀도우 모드 로깅을 수행합니다.
    """
    
    def __init__(self, config_module: Any):
        self.config = config_module
        ticks_per_year = int(getattr(config_module, "TICKS_PER_YEAR", 100))
        self.price_history_shadow: Deque[float] = deque(maxlen=ticks_per_year)
        self.potential_gdp = 0.0

    def decide(self, government: Any, market_data: Dict[str, Any], current_tick: int) -> Dict[str, Any]:
        # 1. Update Price History
        avg_price = market_data.get("avg_goods_price", 10.0)
        self.price_history_shadow.append(avg_price)

        # 2. Calculate Inflation (YoY)
        inflation = 0.0
        if len(self.price_history_shadow) >= 2:
            current_p = self.price_history_shadow[-1]
            past_p = self.price_history_shadow[0]
            if past_p > 0:
                inflation = (current_p - past_p) / past_p

        # 3. Calculate GDP Gap
        current_gdp = market_data.get("total_production", 0.0)
        if self.potential_gdp == 0.0:
            self.potential_gdp = current_gdp
            
        gdp_gap = 0.0
        if self.potential_gdp > 0:
            gdp_gap = (current_gdp - self.potential_gdp) / self.potential_gdp
            # EMA Update for Potential
            alpha = 0.01
            self.potential_gdp = (alpha * current_gdp) + ((1-alpha) * self.potential_gdp)

        # 4. Taylor Rule 2.0 Calculation
        target_inflation = getattr(self.config, "CB_INFLATION_TARGET", 0.02)
        # Neutral Rate assumption: Real Growth (Simplified or Fixed for now)
        neutral_rate = 0.02 
        target_rate = neutral_rate + inflation + 0.5 * (inflation - target_inflation) + 0.5 * gdp_gap

        # 5. Shadow Logging
        current_base_rate = market_data.get("loan_market", {}).get("interest_rate", 0.05)
        log_shadow(
            tick=current_tick,
            agent_id=government.id,
            agent_type="Government",
            metric="taylor_rule_rate",
            current_value=current_base_rate,
            shadow_value=target_rate,
            details=f"Inf={inflation:.2%}, Gap={gdp_gap:.2%}"
        )

        # TaylorRulePolicy는 실제 정책을 변경하지 않고 Shadow만 남기거나, 
        # 필요 시 기본 상태를 반환합니다.
        return {
            "interest_rate_target": target_rate,
            "policy_type": "TAYLOR_RULE"
        }
