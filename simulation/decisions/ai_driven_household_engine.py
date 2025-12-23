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
            
            good_info = self.config_module.GOODS.get(item_id, {})
            utility_effects = good_info.get("utility_effects", {})
            
            # Improved Valuation: Anchor to Market Price + Urgent Need
            avg_price = market_data.get("goods_market", {}).get(f"{item_id}_avg_traded_price", 10.0)
            if not avg_price or avg_price <= 0:
                avg_price = 10.0 # Fallback
                
            # Valuation factor: Use the most pressing need satisfied by this good
            max_need_value = 0.0
            for need_type in utility_effects.keys():
                nv = household.needs.get(need_type, 0.0)
                if nv > max_need_value:
                    max_need_value = nv
            
            # Need Factor: if max_need is 50 (medium), factor is 1.0. If 100, factor is 2.0.
            need_factor = 0.5 + (max_need_value / 100.0)
            valuation_modifier = 0.9 + (agg_buy * 0.2) # 0.9 to 1.1
            
            willingness_to_pay = avg_price * need_factor * valuation_modifier
            
            # 3. Execution: Multi-unit Purchase Logic (Bulk Buying)
            # If need is high (> 70) or agg_buy is very high, buy more units.
            max_q = self.config_module.HOUSEHOLD_MAX_PURCHASE_QUANTITY
            
            target_quantity = 1.0
            
            if max_need_value > 70:
                target_quantity = max_q
            elif agg_buy > 0.8:
                target_quantity = max(1.0, max_q * 0.6) # Moderate panic
            
            # Budget Constraint Check: Don't spend more than 50% of assets on a single item per tick
            # unless survival is critical.
            budget_limit = household.assets * 0.5
            if max_need_value > 80:
                budget_limit = household.assets * 0.9 # Extreme urgency
            
            if willingness_to_pay * target_quantity > budget_limit:
                # Reduce quantity first
                target_quantity = max(1.0, budget_limit / willingness_to_pay)
                # If still too expensive, reduce WTP? No, just buy less.
                if willingness_to_pay * target_quantity > budget_limit:
                    target_quantity = budget_limit / willingness_to_pay
            
            # Final Sanity Check
            if target_quantity >= 0.1 and willingness_to_pay > 0:
                orders.append(
                    Order(household.id, "BUY", item_id, max(1, int(target_quantity)), willingness_to_pay, item_id)
                )

        # 3. Execution: Labor Logic
        labor_market_info = market_data.get("goods_market", {}).get("labor", {})
        market_avg_wage = labor_market_info.get("avg_wage", self.config_module.LABOR_MARKET_MIN_WAGE)
        best_market_offer = labor_market_info.get("best_wage_offer", 0.0)
             
        # Scenario A: Already Employed - Monitor market for better wages
        if household.is_employed:
            # Mobility Lever: AI determines how much of a gap triggers a quit
            agg_mobility = action_vector.job_mobility_aggressiveness
            
            # Threshold: 1.0 (if agg=1.0) to 2.0 (if agg=0.0)
            quit_threshold = 2.0 - agg_mobility
            
            # 1. Quitting if market metrics exceed the threshold
            if (market_avg_wage > household.current_wage * quit_threshold or 
                best_market_offer > household.current_wage * quit_threshold):
                
                # Probability scales with mobility intent
                if random.random() < (0.1 + agg_mobility * 0.9):
                    print(f"DEBUG: Household {household.id} quitting (AI decision). Current: {household.current_wage:.2f}, Threshold: {quit_threshold:.2f}, BestOffer: {best_market_offer:.2f}")
                    household.quit()

        # Scenario B: Unemployed (Default or just quit) - Always look for work
        if not household.is_employed:
            agg_work = action_vector.work_aggressiveness
            # Reservation Wage logic: more aggressive workers accept lower wages
            reservation_modifier = 1.5 - (agg_work * 1.0) # Range [0.5, 1.5]
            reservation_wage = max(self.config_module.LABOR_MARKET_MIN_WAGE, market_avg_wage * reservation_modifier)

            orders.append(
                Order(household.id, "SELL", "labor", 1, reservation_wage, "labor")
            )

        return orders, action_vector

    # Legacy helper methods removed
    def _execute_tactic(self, *args): return []
    def _handle_specific_purchase(self, *args): return []