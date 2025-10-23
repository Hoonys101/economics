from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
import logging

from simulation.models import Order
from simulation.ai.enums import Tactic
from .rule_based_firm_engine import RuleBasedFirmDecisionEngine
from .base_decision_engine import BaseDecisionEngine

if TYPE_CHECKING:
    from simulation.firms import Firm
    from simulation.ai.firm_ai import FirmAI

logger = logging.getLogger(__name__)

class AIDrivenFirmDecisionEngine(BaseDecisionEngine):
    """기업의 AI 기반 의사결정을 담당하는 엔진.

    AI가 전술을 선택하면, 구체적인 실행은 규칙 기반 엔진에 위임한다.
    """
    def __init__(self, ai_engine: FirmAI, config_module: Any, logger: Optional[logging.Logger] = None) -> None:
        """AIDrivenFirmDecisionEngine을 초기화합니다."""
        self.ai_engine = ai_engine
        self.config_module = config_module
        self.logger = logger if logger else logging.getLogger(__name__)
        # AI의 결정을 실행할 규칙 기반 엔진을 내부적으로 소유
        self.rule_based_engine = RuleBasedFirmDecisionEngine(config_module, self.logger)
        self.logger.info("AIDrivenFirmDecisionEngine initialized.", extra={'tick': 0, 'tags': ['init']})

    def make_decisions(self, firm: Firm, markets: Dict[str, Any], goods_data: List[Dict[str, Any]], market_data: Dict[str, Any], current_time: int) -> Tuple[List[Order], Tactic]:
        """
        AI 엔진을 사용하여 최적의 전술을 결정하고, 그에 따른 주문을 생성한다.
        """
        agent_data = firm.get_agent_data()
        pre_state_data = firm.get_pre_state_data()
        
        # AI에게 전술 결정 위임
        chosen_tactic = self.ai_engine.decide_and_learn(agent_data, market_data, pre_state_data)
        
        # 전술에 따른 실행
        orders = self._execute_tactic(chosen_tactic, firm, current_time, market_data)
        
        return orders, chosen_tactic

    def _execute_tactic(self, tactic: Tactic, firm: Firm, current_tick: int, market_data: Dict[str, Any]) -> List[Order]:
        """
        선택된 전술에 따라 실제 행동(주문 생성)을 수행한다.
        모든 실행은 규칙 기반 엔진에 위임한다.
        """
        self.logger.info(f"Firm {firm.id} chose Tactic: {tactic.name}", extra={'tick': current_tick, 'agent_id': firm.id, 'tactic': tactic.name})
        
        # 모든 전술 실행을 규칙 기반 엔진의 내부 메서드에 위임
        if tactic == Tactic.ADJUST_PRODUCTION:
            return self.rule_based_engine._adjust_production(firm, current_tick)
        elif tactic == Tactic.ADJUST_WAGES:
            return self.rule_based_engine._adjust_wages(firm, current_tick, market_data)
        elif tactic == Tactic.ADJUST_PRICE:
            return self.rule_based_engine._adjust_price(firm, current_tick)
        elif tactic in [
            Tactic.PRICE_INCREASE_SMALL, Tactic.PRICE_DECREASE_SMALL,
            Tactic.PRICE_INCREASE_MEDIUM, Tactic.PRICE_DECREASE_MEDIUM,
            Tactic.PRICE_HOLD
        ]:
            return self.rule_based_engine._adjust_price_with_ai(firm, current_tick, tactic)
        
        return []