from typing import Dict, Any, Deque, TYPE_CHECKING, Optional
from collections import deque
from simulation.interfaces.policy_interface import IGovernmentPolicy
from simulation.utils.shadow_logger import log_shadow
from simulation.dtos.policy_dtos import PolicyContextDTO, PolicyDecisionResultDTO

if TYPE_CHECKING:
    pass

class TaylorRulePolicy(IGovernmentPolicy):
    """
    WO-056: 테일러 준칙 기반의 정책 엔진.
    기존의 수식 기반 결정을 담당하며, 섀도우 모드 로깅을 수행합니다.
    """
    
    def __init__(self, config_module: Any):
        self.config = config_module
        ticks_per_year = int(getattr(config_module, "TICKS_PER_YEAR", 100))
        self.price_history_shadow: Deque[float] = deque(maxlen=ticks_per_year)

    def decide(self, context: PolicyContextDTO) -> PolicyDecisionResultDTO:
        sensory_data = context.sensory_data

        if not sensory_data:
            return PolicyDecisionResultDTO(
                policy_type="TAYLOR_RULE",
                status="NO_DATA",
                action_taken="No sensory data received"
            )

        # 2. Use smoothed inflation from DTO
        inflation = sensory_data.inflation_sma

        # 3. Calculate GDP Gap & Update Government State
        current_gdp = sensory_data.current_gdp
        potential_gdp = context.potential_gdp

        if potential_gdp == 0.0:
            potential_gdp = current_gdp

        gdp_gap = 0.0
        if potential_gdp > 0:
            gdp_gap = (current_gdp - potential_gdp) / potential_gdp

        # EMA Update for Potential
        if potential_gdp != 0.0:
            alpha = 0.01
            potential_gdp = (alpha * current_gdp) + ((1-alpha) * potential_gdp)

        # 4. Update Fiscal Stance and Tax Rate
        updated_fiscal_stance = context.fiscal_stance
        updated_income_tax_rate = context.current_income_tax_rate

        if getattr(self.config, "AUTO_COUNTER_CYCLICAL_ENABLED", False):
            sensitivity = getattr(self.config, "FISCAL_SENSITIVITY_ALPHA", 0.5)
            base_tax_rate = getattr(self.config, "INCOME_TAX_RATE", 0.1)

            updated_fiscal_stance = -sensitivity * gdp_gap
            updated_income_tax_rate = base_tax_rate * (1 - updated_fiscal_stance)


        # 5. Taylor Rule (Shadow Logging)
        target_inflation = getattr(self.config, "CB_INFLATION_TARGET", 0.02)
        neutral_rate = 0.02 
        target_rate = neutral_rate + inflation + 0.5 * (inflation - target_inflation) + 0.5 * gdp_gap
        current_base_rate = context.central_bank_base_rate

        log_shadow(
            tick=context.tick,
            agent_id=context.agent_id,
            agent_type="Government",
            metric="taylor_rule_rate",
            current_value=current_base_rate,
            shadow_value=target_rate,
            details=f"Inf={inflation:.2%}, Gap={gdp_gap:.2%}"
        )

        return PolicyDecisionResultDTO(
            interest_rate_target=target_rate,
            policy_type="TAYLOR_RULE",
            status="EXECUTED",
            action_taken="Updated tax rate based on Taylor Rule fiscal stance.",
            updated_potential_gdp=potential_gdp,
            updated_fiscal_stance=updated_fiscal_stance,
            updated_income_tax_rate=updated_income_tax_rate
        )
