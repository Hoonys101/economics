from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
import logging

from simulation.models import Order
from simulation.ai.enums import Tactic, Aggressiveness
from .base_decision_engine import BaseDecisionEngine
from simulation.dtos import DecisionContext

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.ai.household_ai import HouseholdAI

logger = logging.getLogger(__name__)


class AIDrivenHouseholdDecisionEngine(BaseDecisionEngine):
    """가계의 AI 기반 의사결정을 담당하는 엔진."""

    def __init__(
        self,
        ai_engine: HouseholdAI,
        config_module: Any,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.ai_engine = ai_engine
        self.config_module = config_module
        self.logger = logger if logger else logging.getLogger(__name__)
        self.logger.info(
            "AIDrivenHouseholdDecisionEngine initialized.",
            extra={"tick": 0, "tags": ["init"]},
        )

    def make_decisions(
        self,
        context: DecisionContext,
    ) -> Tuple[List[Order], Any]: # Returns HouseholdActionVector
        """
        AI 엔진을 사용하여 최적의 전술(Vector)을 결정하고, 그에 따른 주문을 생성한다.
        Architecture V2: Continuous Aggressiveness
        """
        household = context.household
        markets = context.markets
        market_data = context.market_data
        current_time = context.current_time

        agent_data = household.get_agent_data()

        goods_list = list(self.config_module.GOODS.keys())
        
        # 1. AI Decision (Vector Output)
        action_vector = self.ai_engine.decide_action_vector(
            agent_data, market_data, goods_list
        )
        
        orders = []

        # 2. Execution: Consumption Logic (Per Item)
        for item_id in goods_list:
            agg_buy = action_vector.consumption_aggressiveness.get(item_id, 0.5)
            
            # Willingness to Pay Calculation
            # Base logic: Utility / Marginal Utility of money?
            # Simplified: Budget allocation + Aggressiveness
            
            # Calculate Marginal Utility of this item
            good_info = self.config_module.GOODS.get(item_id, {})
            utility_effects = good_info.get("utility_effects", {})
            current_inventory = household.inventory.get(item_id, 0)
            
            base_utility = 0.0
            for need_key, effect in utility_effects.items():
                current_need = household.needs.get(need_key, 0.0)
                base_utility += current_need * effect
            
            # Diminishing returns
            marginal_utility = max(0.1, base_utility / (current_inventory + 1))
            
            # Aggressiveness modifies perceived value/urgency
            # 0.0 -> Conservative (Valuation * 0.8)
            # 1.0 -> Panic Buy (Valuation * 1.5)
            valuation_modifier = 0.8 + (agg_buy * 0.7) 
            willingness_to_pay = marginal_utility * valuation_modifier
            
            # Budget Constraint Check (Simple: can't spend more than assets)
            if household.assets > 0 and willingness_to_pay > 0:
                # Market Price Check (Limit Order at WTP)
                # Or just submit BUY at WTP? 
                # To be realistic, we check 'Best First', but let's submit Limit Order.
                
                # Sanity: Don't bid crazy amounts (Context cap)
                avg_price = market_data.get("avg_goods_price", 10.0)
                if avg_price > 0 and willingness_to_pay > avg_price * 5.0:
                    willingness_to_pay = avg_price * 5.0 # Cap at 5x avg price
                
                orders.append(
                    Order(household.id, "BUY", item_id, 1, willingness_to_pay, item_id)
                )

        # 3. Execution: Labor Logic
        # Always evaluate working
        if not household.is_employed:
            agg_work = action_vector.work_aggressiveness
            
            # Reservation Wage logic
            # 0.0 -> High Wage (Avg * 1.5)
            # 1.0 -> Low Wage (Avg * 0.5)
            market_wage = self.config_module.LABOR_MARKET_MIN_WAGE
            if "labor" in market_data and "avg_wage" in market_data["labor"]:
                 market_wage = market_data["labor"]["avg_wage"]
            
            reservation_modifier = 1.5 - (agg_work * 1.0)
            reservation_wage = max(self.config_module.LABOR_MARKET_MIN_WAGE, market_wage * reservation_modifier)
            
            # Submit SELL order for Labor
            orders.append(
                Order(household.id, "SELL", "labor", 1, reservation_wage, "labor")
            )

        return orders, action_vector

    # Legacy helper methods removed
    def _execute_tactic(self, *args): return []
    def _handle_specific_purchase(self, *args): return []