from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
import logging

from simulation.models import Order
from simulation.ai.enums import Tactic, Aggressiveness
from .base_decision_engine import BaseDecisionEngine
from .rule_based_firm_engine import RuleBasedFirmDecisionEngine
from simulation.dtos import DecisionContext

if TYPE_CHECKING:
    from simulation.firms import Firm

logger = logging.getLogger(__name__)


class StandaloneRuleBasedFirmDecisionEngine(BaseDecisionEngine):
    """
    기업의 규칙 기반 의사결정을 담당하는 독립형 엔진.
    AI가 없는 환경에서 기업의 기본적인 경제 활동을 시뮬레이션한다.
    RuleBasedFirmDecisionEngine의 기능을 활용한다.
    """

    def __init__(
        self,
        config_module: Any,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.config_module = config_module
        self.logger = logger if logger else logging.getLogger(__name__)
        self.rule_based_executor = RuleBasedFirmDecisionEngine(config_module, self.logger)
        self.logger.info(
            "StandaloneRuleBasedFirmDecisionEngine initialized.",
            extra={"tick": 0, "tags": ["init"]},
        )

    def make_decisions(
        self,
        context: DecisionContext,
    ) -> Tuple[List[Order], Tuple[Tactic, Aggressiveness]]:
        """
        규칙 기반 로직을 사용하여 기업의 의사결정을 수행한다.
        생산 조정, 임금 조정, 가격 조정에 집중한다.
        """
        firm = context.firm
        markets = context.markets
        goods_data = context.goods_data
        market_data = context.market_data
        current_time = context.current_time

        if firm is None:
            return [], (Tactic.NO_ACTION, Aggressiveness.NEUTRAL)
        orders: List[Order] = []
        chosen_tactic: Tactic = Tactic.NO_ACTION
        chosen_aggressiveness: Aggressiveness = Aggressiveness.NEUTRAL # 규칙 기반은 중립으로 설정

        item_id = firm.specialization
        current_inventory = firm.inventory.get(item_id, 0)
        target_quantity = firm.production_target

        # 1. 생산 조정 결정 (Planning)
        if current_inventory > target_quantity * self.config_module.OVERSTOCK_THRESHOLD:
            chosen_tactic = Tactic.ADJUST_PRODUCTION
            orders.extend(self.rule_based_executor._adjust_production(firm, current_time))
            self.logger.info(
                f"Firm {firm.id} RuleBased: Overstocked, adjusting production.",
                extra={"tick": current_time, "agent_id": firm.id, "tactic": Tactic.ADJUST_PRODUCTION.name}
            )
        elif current_inventory < target_quantity * self.config_module.UNDERSTOCK_THRESHOLD:
            chosen_tactic = Tactic.ADJUST_PRODUCTION
            orders.extend(self.rule_based_executor._adjust_production(firm, current_time))
            self.logger.info(
                f"Firm {firm.id} RuleBased: Understocked, adjusting production.",
                extra={"tick": current_time, "agent_id": firm.id, "tactic": Tactic.ADJUST_PRODUCTION.name}
            )

        # 2. 임금 조정 및 고용 결정 (Operation)
        # WO-110: Sequential execution - Check labor needs even if production was adjusted
        needed_labor_for_production = self.rule_based_executor._calculate_needed_labor(firm)
        current_employees = len(firm.hr.employees)

        # SoC Refactor: use hr.employees
        # Hiring Logic
        if current_employees < needed_labor_for_production * self.config_module.FIRM_LABOR_REQUIREMENT_RATIO or \
           current_employees < self.config_module.FIRM_MIN_EMPLOYEES:

            if chosen_tactic == Tactic.NO_ACTION:
                chosen_tactic = Tactic.ADJUST_WAGES

            orders.extend(self.rule_based_executor._adjust_wages(firm, current_time, market_data))
            self.logger.info(
                f"Firm {firm.id} RuleBased: Need more labor, adjusting wages/hiring.",
                extra={"tick": current_time, "agent_id": firm.id, "tactic": Tactic.ADJUST_WAGES.name}
            )

        # Firing Logic (WO-110)
        # If overstocked (production target reduced), we may have excess labor.
        firing_buffer_ratio = getattr(self.config_module, "LABOR_FIRING_BUFFER_RATIO", 1.05)
        if current_employees > needed_labor_for_production * firing_buffer_ratio:
             # WO-110 Fix: Labor Hoarding to prevent Demand Collapse.
             # Only fire if we are actually losing money for a sustained period or running low on cash.
             # If we are profitable or have huge reserves, keep employees to sustain the economy (Demand side).
             loss_threshold = getattr(self.config_module, "LABOR_HOARDING_LOSS_THRESHOLD", 5)
             is_bleeding = firm.finance.consecutive_loss_turns > loss_threshold

             startup_cost = getattr(self.config_module, "STARTUP_COST", 30000.0)
             asset_ratio_threshold = getattr(self.config_module, "LABOR_HOARDING_ASSET_RATIO", 0.5)
             is_poor = firm.assets < startup_cost * asset_ratio_threshold

             if is_bleeding or is_poor:
                 # Fire excess
                 self.rule_based_executor._fire_excess_labor(firm, needed_labor_for_production)
                 # _fire_excess_labor returns [] orders but performs action.
                 self.logger.info(
                    f"Firm {firm.id} RuleBased: Excess labor ({current_employees} > {needed_labor_for_production:.1f}), firing due to financial pressure (LossTicks={firm.finance.consecutive_loss_turns}).",
                    extra={"tick": current_time, "agent_id": firm.id, "tactic": "FIRING"}
                )
             else:
                 self.logger.info(
                    f"Firm {firm.id} RuleBased: Excess labor ({current_employees} > {needed_labor_for_production:.1f}), but hoarding labor (LossTicks={firm.finance.consecutive_loss_turns}).",
                    extra={"tick": current_time, "agent_id": firm.id, "tactic": "HOARDING"}
                )

        # 3. 가격 조정 및 판매 (Commerce)
        if current_inventory > 0:
            # Decide on price tactic primarily if no other tactic was chosen, but execute selling regardless.
            if chosen_tactic == Tactic.NO_ACTION:
                # 간단한 규칙: 재고가 많으면 가격을 낮추고, 적으면 가격 유지 또는 높임
                if current_inventory > firm.production_target * self.config_module.OVERSTOCK_THRESHOLD:
                    chosen_tactic = Tactic.PRICE_DECREASE_SMALL # 가격 인하
                else:
                    chosen_tactic = Tactic.PRICE_HOLD # 가격 유지 (또는 AI처럼 동적 조정)

            orders.extend(self._adjust_price_based_on_inventory(firm, current_time))
            self.logger.info(
                f"Firm {firm.id} RuleBased: Adjusting price and selling.",
                extra={"tick": current_time, "agent_id": firm.id, "tactic": Tactic.ADJUST_PRICE.name}
            )

        return orders, (chosen_tactic, chosen_aggressiveness)
    
    def _adjust_price_based_on_inventory(self, firm: Firm, current_tick: int) -> List[Order]:
        """
        재고 수준에 따라 판매 가격을 조정하고 판매 주문을 생성한다.
        AIDrivenFirmDecisionEngine의 _adjust_price 메서드와 유사하게 구현.
        """
        orders = []
        item_id = firm.specialization
        current_inventory = firm.inventory.get(item_id, 0)

        if current_inventory > 0:
            target_inventory = firm.production_target
            is_understocked = (
                current_inventory
                < target_inventory * self.config_module.UNDERSTOCK_THRESHOLD
            )

            base_price = firm.last_prices.get(
                item_id, self.config_module.GOODS[item_id]["production_cost"]
            )

            adjusted_price = base_price
            if target_inventory > 0:
                diff_ratio = (
                    current_inventory - target_inventory
                ) / target_inventory
                
                # --- Genesis: Acceleration & Emergency Sale (WO-Diag-005) ---
                price_multiplier = getattr(self.config_module, "GENESIS_PRICE_ADJUSTMENT_MULTIPLIER", 1.0)
                
                # Check for Emergency Overstock (2x threshold)
                if current_inventory > 2 * target_inventory * self.config_module.OVERSTOCK_THRESHOLD:
                    # Step-change drop: Force 50% discount to clear dead stock
                    adjusted_price = min(base_price * 0.5, self.config_module.GOODS[item_id]["production_cost"] * 0.5)
                    self.logger.warning(
                        f"EMERGENCY_FIRE_SALE | Firm {firm.id} is severely overstocked ({current_inventory:.1f}). Force-cutting price to {adjusted_price:.2f}",
                        extra={"tick": current_tick, "agent_id": firm.id}
                    )
                else:
                    signed_power = (
                        abs(diff_ratio) ** self.config_module.PRICE_ADJUSTMENT_EXPONENT
                    )
                    # Apply multiplier to speed up price discovery
                    adjustment = signed_power * self.config_module.PRICE_ADJUSTMENT_FACTOR * price_multiplier
                    
                    if diff_ratio < 0: # Understocked, increase price
                        adjusted_price = base_price * (1 + adjustment)
                    else: # Overstocked, decrease price
                        adjusted_price = base_price * (1 - adjustment)
                # ------------------------------------------------------------

            final_price = max(
                getattr(self.config_module, "MIN_SELL_PRICE", 0.1), # Use config floor
                min(self.config_module.MAX_SELL_PRICE, adjusted_price),
            )
            # SoC Refactor: use sales.set_price
            firm.sales.set_price(item_id, final_price)

            quantity_to_sell = min(
                current_inventory, self.config_module.MAX_SELL_QUANTITY
            )
            if quantity_to_sell > 0:
                order = Order(
                    firm.id,
                    "SELL",
                    item_id,
                    quantity_to_sell,
                    final_price,
                    item_id, # FIX: Use item_id as market_id (assumes market_id matches item_id)
                )
                orders.append(order)
                self.logger.info(
                    f"Firm {firm.id} RuleBased Price Adj: Selling {quantity_to_sell:.1f} of {item_id} at price {final_price:.2f}",
                    extra={
                        "tick": current_tick,
                        "agent_id": firm.id,
                        "tags": ["sell_order"],
                    },
                )
        return orders
