from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
import logging
import random

from simulation.models import Order
from simulation.ai.enums import Tactic, Aggressiveness
from .base_decision_engine import BaseDecisionEngine
from simulation.dtos import DecisionContext
from simulation.decisions.corporate_manager import CorporateManager

if TYPE_CHECKING:
    from simulation.firms import Firm
    from simulation.ai.firm_ai import FirmAI

logger = logging.getLogger(__name__)


class AIDrivenFirmDecisionEngine(BaseDecisionEngine):
    """기업의 AI 기반 의사결정을 담당하는 엔진.
    AI (FirmAI) -> Aggressiveness Vector -> CorporateManager -> Orders
    """

    def __init__(
        self,
        ai_engine: FirmAI,
        config_module: Any,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """AIDrivenFirmDecisionEngine을 초기화합니다."""
        self.ai_engine = ai_engine
        self.config_module = config_module
        self.logger = logger if logger else logging.getLogger(__name__)

        # Corporate Manager (The CEO Module)
        self.corporate_manager = CorporateManager(config_module, self.logger)

        self.logger.info(
            "AIDrivenFirmDecisionEngine initialized with CorporateManager.",
            extra={"tick": 0, "tags": ["init"]},
        )

    def make_decisions(
        self,
        context: DecisionContext,
    ) -> Tuple[List[Order], Any]:  # Returns FirmActionVector
        """
        Main Decision Loop.
        1. AI decides Strategy (Vector).
        2. CorporateManager executes Strategy (Orders/Actions).
        """
        firm_state = context.state

        # 1. AI Strategy Decision (Vector Output)
        agent_data = firm_state.agent_data
        action_vector = self.ai_engine.decide_action_vector(
            agent_data, context.market_data
        )

        # 2. Corporate Manager Execution
        orders = self.corporate_manager.realize_ceo_actions(
            firm_state, context, action_vector
        )

        return orders, action_vector
