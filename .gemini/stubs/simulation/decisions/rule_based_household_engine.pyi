import logging
from .base_decision_engine import BaseDecisionEngine as BaseDecisionEngine
from _typeshed import Incomplete
from modules.household.dtos import HouseholdStateDTO as HouseholdStateDTO
from simulation.ai.enums import Aggressiveness as Aggressiveness, Tactic as Tactic
from simulation.dtos import DecisionContext as DecisionContext, DecisionOutputDTO as DecisionOutputDTO, HouseholdConfigDTO as HouseholdConfigDTO, MacroFinancialContext as MacroFinancialContext
from simulation.models import Order as Order
from typing import Any

logger: Incomplete

class RuleBasedHouseholdDecisionEngine(BaseDecisionEngine):
    """
    가계의 규칙 기반 의사결정을 담당하는 엔진.
    AI가 없는 환경에서 가계의 기본적인 경제 활동을 시뮬레이션한다.
    Pure Function: Only uses DecisionContext.state and DecisionContext.config.
    """
    config_module: Incomplete
    logger: Incomplete
    def __init__(self, config_module: Any, logger: logging.Logger | None = None) -> None: ...
