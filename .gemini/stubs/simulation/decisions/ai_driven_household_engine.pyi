import logging
from .base_decision_engine import BaseDecisionEngine as BaseDecisionEngine
from _typeshed import Incomplete
from modules.household.dtos import HouseholdStateDTO as HouseholdStateDTO
from simulation.ai.household_ai import HouseholdAI as HouseholdAI
from simulation.decisions.household.api import AssetManagementContext as AssetManagementContext, ConsumptionContext as ConsumptionContext, LaborContext as LaborContext
from simulation.decisions.household.asset_manager import AssetManager as AssetManager
from simulation.decisions.household.consumption_manager import ConsumptionManager as ConsumptionManager
from simulation.decisions.household.labor_manager import LaborManager as LaborManager
from simulation.dtos import DecisionContext as DecisionContext, DecisionOutputDTO as DecisionOutputDTO, HouseholdConfigDTO as HouseholdConfigDTO, MacroFinancialContext as MacroFinancialContext
from simulation.models import Order as Order
from typing import Any

logger: Incomplete

class AIDrivenHouseholdDecisionEngine(BaseDecisionEngine):
    """가계의 AI 기반 의사결정을 담당하는 엔진 (Refactored to Coordinator Pattern)."""
    ai_engine: Incomplete
    config_module: Incomplete
    logger: Incomplete
    consumption_manager: Incomplete
    labor_manager: Incomplete
    asset_manager: Incomplete
    def __init__(self, ai_engine: HouseholdAI, config_module: Any, logger: logging.Logger | None = None) -> None: ...
    def decide_reproduction(self, context: DecisionContext) -> bool:
        """
        Calls AI engine to decide reproduction.
        """
