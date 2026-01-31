from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
import logging

from simulation.models import Order
from .base_decision_engine import BaseDecisionEngine
from simulation.dtos import DecisionContext, MacroFinancialContext, DecisionOutputDTO

# Modular Managers
from simulation.decisions.household.api import (
    ConsumptionContext, LaborContext, AssetManagementContext, HousingContext
)
from simulation.decisions.household.consumption_manager import ConsumptionManager
from simulation.decisions.household.labor_manager import LaborManager
from simulation.decisions.household.asset_manager import AssetManager
from simulation.decisions.household.housing_manager import HousingManager

if TYPE_CHECKING:
    from simulation.ai.household_ai import HouseholdAI
    from modules.household.dtos import HouseholdStateDTO
    from simulation.dtos import HouseholdConfigDTO

logger = logging.getLogger(__name__)


class AIDrivenHouseholdDecisionEngine(BaseDecisionEngine):
    """가계의 AI 기반 의사결정을 담당하는 엔진 (Refactored to Coordinator Pattern)."""

    def __init__(
        self,
        ai_engine: HouseholdAI,
        config_module: Any,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.ai_engine = ai_engine
        self.config_module = config_module
        self.logger = logger if logger else logging.getLogger(__name__)

        # Initialize Managers
        self.consumption_manager = ConsumptionManager()
        self.labor_manager = LaborManager()
        self.asset_manager = AssetManager()
        self.housing_manager = HousingManager(logger=self.logger)

        self.logger.info(
            "AIDrivenHouseholdDecisionEngine initialized (Modularized).",
            extra={"tick": 0, "tags": ["init"]},
        )

    def _make_decisions_internal(
        self,
        context: DecisionContext,
        macro_context: Optional[MacroFinancialContext] = None,
    ) -> DecisionOutputDTO:
        """
        AI 엔진을 사용하여 최적의 전술(Vector)을 결정하고, 그에 따른 주문을 생성한다.
        """
        household: HouseholdStateDTO = context.state
        config: HouseholdConfigDTO = context.config

        if household is None:
            from simulation.schemas import HouseholdActionVector
            return DecisionOutputDTO(orders=[], metadata=HouseholdActionVector())

        market_snapshot = context.market_snapshot
        market_data = context.market_data
        current_time = context.current_time

        # --- Phase 2: Survival Override ---
        # Delegated to ConsumptionManager
        survival_override_result = self.consumption_manager.check_survival_override(
            household, config, market_snapshot, current_time, self.logger
        )

        if survival_override_result:
            res_orders, res_vector = survival_override_result
            return DecisionOutputDTO(orders=res_orders, metadata=res_vector)


        agent_data = household.agent_data

        goods_list = list(config.goods.keys())
        
        action_vector = self.ai_engine.decide_action_vector(
            agent_data, market_data, goods_list
        )
        
        # 1. Asset Manager (ROI Calculation Helper)
        # Note: Logic required savings_roi BEFORE consumption logic.
        savings_roi = self.asset_manager.get_savings_roi(household, market_data, config)
        # Apply 3-Pillars Preference (Wealth Pillar) - Parity with Legacy
        savings_roi *= household.preference_asset
        
        debt_penalty = self.asset_manager.get_debt_penalty(household, market_data, config)
        
        orders = []

        # 2. Consumption
        cons_ctx = ConsumptionContext(
            household=household, config=config, market_data=market_data,
            action_vector=action_vector, savings_roi=savings_roi,
            debt_penalty=debt_penalty, stress_config=context.stress_scenario_config,
            logger=self.logger
        )
        orders.extend(self.consumption_manager.decide_consumption(cons_ctx))
        
        # 3. Labor
        labor_ctx = LaborContext(
            household=household, config=config, market_data=market_data,
            action_vector=action_vector, current_time=current_time,
            logger=self.logger
        )
        orders.extend(self.labor_manager.decide_labor(labor_ctx))
        
        # 4. Asset / Investment
        asset_ctx = AssetManagementContext(
            household=household, config=config, market_data=market_data,
            market_snapshot=market_snapshot, macro_context=macro_context,
            action_vector=action_vector, current_time=current_time,
            stress_config=context.stress_scenario_config, logger=self.logger
        )
        orders.extend(self.asset_manager.decide_investments(asset_ctx))
        
        # 5. Housing
        housing_ctx = HousingContext(
             household=household, config=config, market_data=market_data,
             market_snapshot=market_snapshot, current_time=current_time,
             stress_config=context.stress_scenario_config, logger=self.logger
        )
        orders.extend(self.housing_manager.decide_housing(housing_ctx))
        
        return DecisionOutputDTO(orders=orders, metadata=action_vector)

    def decide_reproduction(self, context: DecisionContext) -> bool:
        """
        Calls AI engine to decide reproduction.
        """
        household = context.state
        if not household: return False

        agent_data = household.agent_data
        market_data = context.market_data

        return self.ai_engine.decide_reproduction(agent_data, market_data, context.current_time)
