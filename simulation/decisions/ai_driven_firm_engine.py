from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
import logging

from simulation.models import Order
from simulation.ai.enums import Tactic, Aggressiveness
from .rule_based_firm_engine import RuleBasedFirmDecisionEngine
from .base_decision_engine import BaseDecisionEngine
from simulation.dtos import DecisionContext

if TYPE_CHECKING:
    from simulation.firms import Firm
    from simulation.ai.firm_ai import FirmAI

logger = logging.getLogger(__name__)


class AIDrivenFirmDecisionEngine(BaseDecisionEngine):
    """기업의 AI 기반 의사결정을 담당하는 엔진.

    AI가 전술을 선택하면, 구체적인 실행은 규칙 기반 엔진에 위임한다.
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
        # AI의 결정을 실행할 규칙 기반 엔진을 내부적으로 소유
        self.rule_based_engine = RuleBasedFirmDecisionEngine(config_module, self.logger)
        self.logger.info(
            "AIDrivenFirmDecisionEngine initialized.",
            extra={"tick": 0, "tags": ["init"]},
        )

    def make_decisions(
        self,
        context: DecisionContext,
    ) -> Tuple[List[Order], Any]: # Returns FirmActionVector
        """
        AI 엔진을 사용하여 최적의 전술(Vector)을 결정하고, 그에 따른 주문을 생성한다.
        Architecture V2: Continuous Aggressiveness
        """
        firm = context.firm
        if firm is None:
             raise ValueError("Firm must be provided in context for FirmDecisionEngine")

        markets = context.markets
        market_data = context.market_data
        current_time = context.current_time
        agent_data = firm.get_agent_data()

        # 1. AI Decision (Vector Output)
        action_vector = self.ai_engine.decide_action_vector(
            agent_data, market_data
        )

        orders = []

        # 2. Execution: Sales Logic
        # Always attempt to sell if we have inventory
        item_id = firm.specialization
        current_inventory = firm.inventory.get(item_id, 0)
        
        if current_inventory > 0:
            # Anchor Price Selection:
            # 1. Market Data (Current traded price in the whole market)
            # 2. Firm's last successful(? or attempted) price 
            # 3. Production Cost (Fundamental floor)
            
            market_price = 0.0
            
            # Use market_data if available (from context)
            if item_id in market_data:
                 market_price = market_data[item_id].get('avg_price', 0)
            
            # If not in market_data root, check goods_market_data format (from engine._prepare_market_data)
            if market_price <= 0:
                 market_price = market_data.get(f"{item_id}_current_sell_price", 0)
            
            # Firm's own memory
            if market_price <= 0:
                 market_price = firm.last_prices.get(item_id, 0)
            
            # Absolute fallback
            if market_price <= 0:
                 market_price = self.config_module.GOODS[item_id].get("production_cost", 10.0)
            
            # Pricing Lever: Aggressiveness 
            # 0.0 -> Try to sell at Premium (+20%)
            # 1.0 -> Try to sell at Discount (-20%)
            agg_sell = action_vector.sales_aggressiveness
            price_adjustment = (0.5 - agg_sell) * 0.4 # +/- 20% range
            
            target_price = market_price * (1.0 + price_adjustment)
            final_price = max(0.1, target_price) # Prevent negative/zero
            
            firm.last_prices[item_id] = final_price # Update memory
            
            qty = min(current_inventory, self.config_module.MAX_SELL_QUANTITY)
            if qty > 0:
                orders.append(
                    Order(firm.id, "SELL", item_id, qty, final_price, item_id)
                )

        # 3. Execution: Hiring Logic
        target_inventory = firm.production_target
        inventory_gap = target_inventory - current_inventory
        
        if inventory_gap > 0:
             # Heuristic: base needed labor on production missing
             # (Each labor unit produces roughly firm.productivity_factor)
             needed_labor = max(1, int(inventory_gap / firm.productivity_factor))
             needed_labor = min(needed_labor, 5) # Cap hiring per tick
             
             # Hiring Lever: Aggressiveness from AI
             agg_hire = action_vector.hiring_aggressiveness
             
             # Internal Urgency Modifier
             urgency = min(1.0, inventory_gap / target_inventory) if target_inventory > 0 else 1.0
             
             market_wage = self.config_module.LABOR_MARKET_MIN_WAGE
             if "labor" in market_data and "avg_wage" in market_data["labor"]:
                 market_wage = market_data["labor"]["avg_wage"]
             
             # Combined Wage Logic: AI Aggressiveness + Urgency
             # 0.5 is neutral. 1.0 is aggressive.
             effective_agg = (agg_hire * 0.5) + (urgency * 0.5)
             
             # Range: -20% to +50% of market wage
             wage_adjustment = -0.2 + (effective_agg * 0.7) 
             
             if len(firm.employees) == 0:
                 # Desperate to start production!
                 wage_adjustment = max(wage_adjustment, 0.3)
                 
             offer_wage = market_wage * (1.0 + wage_adjustment)
             offer_wage = max(self.config_module.LABOR_MARKET_MIN_WAGE, offer_wage)
             print(f"DEBUG: Firm {firm.id} offering wage: {offer_wage:.2f} (Urgency: {urgency:.2f}, Agg: {agg_hire:.2f})")
             
             for _ in range(needed_labor):
                 orders.append(
                     Order(firm.id, "BUY", "labor", 1, offer_wage, "labor")
                 )

        return orders, action_vector

    # Legacy helper methods removed as they are integrated into vector execution logic
    def _execute_tactic(self, *args): return []
    def _adjust_price(self, *args): return []
    def _adjust_price_with_ai(self, *args): return []
