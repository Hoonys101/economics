import logging
from .base_decision_engine import BaseDecisionEngine as BaseDecisionEngine
from .rule_based_firm_engine import RuleBasedFirmDecisionEngine as RuleBasedFirmDecisionEngine
from _typeshed import Incomplete
from simulation.ai.enums import Aggressiveness as Aggressiveness, Tactic as Tactic
from simulation.dtos import DecisionContext as DecisionContext, DecisionOutputDTO as DecisionOutputDTO, FirmStateDTO as FirmStateDTO
from simulation.firms import Firm as Firm
from simulation.models import Order as Order
from typing import Any

logger: Incomplete

class StandaloneRuleBasedFirmDecisionEngine(BaseDecisionEngine):
    """
    기업의 규칙 기반 의사결정을 담당하는 독립형 엔진.
    AI가 없는 환경에서 기업의 기본적인 경제 활동을 시뮬레이션한다.
    RuleBasedFirmDecisionEngine의 기능을 활용한다.
    Refactored for DTO Purity Gate (WO-114).
    """
    config_module: Incomplete
    logger: Incomplete
    rule_based_executor: Incomplete
    def __init__(self, config_module: Any, logger: logging.Logger | None = None) -> None: ...
