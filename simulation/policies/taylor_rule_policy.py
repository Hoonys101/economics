from typing import Dict, Any, Deque, TYPE_CHECKING
from collections import deque
from simulation.interfaces.policy_interface import IGovernmentPolicy
from modules.common.utils.shadow_logger import log_shadow

if TYPE_CHECKING:
    from simulation.dtos import GovernmentStateDTO

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

    def decide(self, government: Any, sensory_data: "GovernmentStateDTO", current_tick: int, central_bank: Any) -> Dict[str, Any]:
        # Refactored to use sensory DTO instead of raw market_data
        if not sensory_data:
            return {"status": "NO_DATA"}

        # 2. Use smoothed inflation from DTO
        inflation = sensory_data.inflation_sma

        # 3. Calculate GDP Gap & Update Government State
        current_gdp = sensory_data.current_gdp
        if government.potential_gdp == 0.0:
            government.potential_gdp = current_gdp

        gdp_gap = 0.0
        if government.potential_gdp > 0:
            gdp_gap = (current_gdp - government.potential_gdp) / government.potential_gdp

        # EMA Update for Potential
        if government.potential_gdp != 0.0:
            alpha = 0.01
            government.potential_gdp = (alpha * current_gdp) + ((1-alpha) * government.potential_gdp)

        # 4. Update Fiscal Stance and Tax Rate
        if getattr(self.config, "AUTO_COUNTER_CYCLICAL_ENABLED", False):
            sensitivity = getattr(self.config, "FISCAL_SENSITIVITY_ALPHA", 0.5)
            base_tax_rate = getattr(self.config, "INCOME_TAX_RATE", 0.1)

            government.fiscal_stance = -sensitivity * gdp_gap
            new_tax_rate = base_tax_rate * (1 - government.fiscal_stance)
            government.income_tax_rate = new_tax_rate


        # 5. Taylor Rule (Shadow Logging)
        target_inflation = getattr(self.config, "CB_INFLATION_TARGET", 0.02)
        neutral_rate = 0.02 
        target_rate = neutral_rate + inflation + 0.5 * (inflation - target_inflation) + 0.5 * gdp_gap
        current_base_rate = central_bank.get_base_rate()
        log_shadow(
            tick=current_tick,
            agent_id=government.id,
            agent_type="Government",
            metric="taylor_rule_rate",
            current_value=current_base_rate,
            shadow_value=target_rate,
            details=f"Inf={inflation:.2%}, Gap={gdp_gap:.2%}"
        )

        return {
            "interest_rate_target": target_rate,
            "policy_type": "TAYLOR_RULE",
            "status": "EXECUTED",
            "action_taken": "Updated tax rate based on Taylor Rule fiscal stance."
        }
