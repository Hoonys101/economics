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

        # 1. 생산 조정 결정
        if current_inventory > target_quantity * self.config_module.OVERSTOCK_THRESHOLD:
            chosen_tactic = Tactic.ADJUST_PRODUCTION
            orders.extend(self.rule_based_executor._adjust_production(firm, current_time))
            self.logger.info(
                f"Firm {firm.id} RuleBased: Overstocked, adjusting production.",
                extra={"tick": current_time, "agent_id": firm.id, "tactic": chosen_tactic.name}
            )
        elif current_inventory < target_quantity * self.config_module.UNDERSTOCK_THRESHOLD:
            chosen_tactic = Tactic.ADJUST_PRODUCTION
            orders.extend(self.rule_based_executor._adjust_production(firm, current_time))
            self.logger.info(
                f"Firm {firm.id} RuleBased: Understocked, adjusting production.",
                extra={"tick": current_time, "agent_id": firm.id, "tactic": chosen_tactic.name}
            )

        # [FIX: WO-Diag-005] Kickstart Production Logic
        # If inventory is wiped out (Fire-Sale) and target is too low (due to cuts),
        # the firm must aggressively restart production to meet demand.
        # Threshold 50.0 is approx 5 employees' worth of output (Productivity 10.0).
        if current_inventory < 5.0 and firm.production_target < 50.0:
            old_target = firm.production_target
            firm.production_target = 50.0
            self.logger.warning(
                f"KICKSTART_PRODUCTION | Firm {firm.id} rebooting capacity. {old_target:.1f} -> {firm.production_target:.1f}",
                extra={"tick": current_time, "agent_id": firm.id, "tags": ["kickstart"]}
            )

        # 2. 임금 조정 및 고용 결정 (생산 조정 이후 필요에 따라)
        # [FIX: WO-Diag-005] Allow simultaneous Production Adjustment and Hiring
        # Previously, if tactic was ADJUST_PRODUCTION, we skipped hiring. This caused a death spiral
        # where firms increased targets (due to understock) but never hired the labor to meet them.
        needed_labor_for_production = self.rule_based_executor._calculate_needed_labor(firm)
        if len(firm.employees) < needed_labor_for_production * self.config_module.FIRM_LABOR_REQUIREMENT_RATIO or \
            len(firm.employees) < self.config_module.FIRM_MIN_EMPLOYEES:

            # If we are already adjusting production, we might want to keep that label or switch to wages.
            # We prioritize executing the action.
            chosen_tactic = Tactic.ADJUST_WAGES
            labor_orders = self.rule_based_executor._adjust_wages(firm, current_time, market_data)

            # [FIX: WO-Diag-005] Solvency-Based Wage Offer
            # If firm revenue crashed (due to Fire-Sale), it cannot pay BASE_WAGE.
            # It must offer what it can afford (Sustainable Wage), matching the Household's Wage Surrender.
            for order in labor_orders:
                if order.order_type == "BUY" and order.market_id == "labor_market":
                    last_price = firm.last_prices.get(firm.specialization, self.config_module.GOODS[firm.specialization]["production_cost"])
                    # Sustainable Wage = Revenue per Worker * Margin Safety (0.9)
                    sustainable_wage = (last_price * firm.productivity_factor) * 0.9

                    original_offer = order.price
                    # Offer lower of (Original, Sustainable), but at least 1.0
                    new_offer = max(1.0, min(original_offer, sustainable_wage))

                    if new_offer < original_offer:
                        order.price = new_offer
                        self.logger.warning(
                            f"SOLVENCY_WAGE_ADJ | Firm {firm.id} lowering wage offer. {original_offer:.2f} -> {new_offer:.2f} (Sustainable: {sustainable_wage:.2f})",
                            extra={"tick": current_time, "agent_id": firm.id, "tags": ["wage_adjustment"]}
                        )

            orders.extend(labor_orders)
            self.logger.info(
                f"Firm {firm.id} RuleBased: Need more labor, adjusting wages/hiring.",
                extra={"tick": current_time, "agent_id": firm.id, "tactic": chosen_tactic.name}
            )

        # 3. 가격 조정 및 판매 (재고가 있을 경우)
        if current_inventory > 0:
            if chosen_tactic not in [Tactic.ADJUST_PRODUCTION, Tactic.ADJUST_WAGES]: # 다른 전술 결정이 없었으면 가격 조정
                # 간단한 규칙: 재고가 많으면 가격을 낮추고, 적으면 가격 유지 또는 높임
                if current_inventory > firm.production_target * self.config_module.OVERSTOCK_THRESHOLD:
                    chosen_tactic = Tactic.PRICE_DECREASE_SMALL # 가격 인하
                else:
                    chosen_tactic = Tactic.PRICE_HOLD # 가격 유지 (또는 AI처럼 동적 조정)

                # RuleBasedFirmDecisionEngine에는 가격 조정 메서드가 없으므로, 여기에 간단히 구현하거나
                # _adjust_price_with_ai와 유사한 메서드를 RuleBasedFirmDecisionEngine에 추가하는 것을 고려해야 한다.
                # 현재는 AIDrivenFirmDecisionEngine의 _adjust_price를 참조하여 유사하게 구현 (재고 기반 가격 조정)
                orders.extend(self._adjust_price_based_on_inventory(firm, current_time))
                self.logger.info(
                    f"Firm {firm.id} RuleBased: Adjusting price and selling.",
                    extra={"tick": current_time, "agent_id": firm.id, "tactic": chosen_tactic.name}
                )

        # 기본 전술 반환 (만약 아무것도 선택되지 않았다면 NO_ACTION)
        if chosen_tactic == Tactic.NO_ACTION:
            # Fallback for pricing, always attempt to sell if inventory exists.
            if current_inventory > 0:
                orders.extend(self._adjust_price_based_on_inventory(firm, current_time))
                chosen_tactic = Tactic.PRICE_HOLD # Placeholder, as some action was taken
                self.logger.info(
                    f"Firm {firm.id} RuleBased: Defaulting to price adjustment/selling.",
                    extra={"tick": current_time, "agent_id": firm.id, "tactic": chosen_tactic.name}
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

            # --- Genesis: Fire-Sale Logic (WO-Diag-005) ---
            # 1. Emergency Fire-Sale
            # If inventory is excessively high (e.g. 2x threshold), crash the price.
            # Strategy: Step-change drop to 50% of current or cost.
            is_emergency_overstock = (
                current_inventory > target_inventory * self.config_module.OVERSTOCK_THRESHOLD * 2.0
            )

            if is_emergency_overstock:
                production_cost = self.config_module.GOODS[item_id]["production_cost"]
                adjusted_price = max(base_price * 0.5, production_cost * 0.5)
                self.logger.warning(
                    f"EMERGENCY_FIRE_SALE | Firm {firm.id} slashing price. Base: {base_price:.2f} -> New: {adjusted_price:.2f}. Inventory: {current_inventory:.1f}",
                    extra={"tick": current_tick, "agent_id": firm.id, "tags": ["fire_sale"]}
                )

            # 2. Standard Adjustment (Boosted by Genesis Factor)
            elif target_inventory > 0:
                diff_ratio = (
                    current_inventory - target_inventory
                ) / target_inventory
                signed_power = (
                    abs(diff_ratio) ** self.config_module.PRICE_ADJUSTMENT_EXPONENT
                )

                # Apply Genesis Multiplier for faster correction
                adjustment_factor = (
                    self.config_module.PRICE_ADJUSTMENT_FACTOR *
                    self.config_module.GENESIS_PRICE_ADJUSTMENT_MULTIPLIER
                )

                if diff_ratio < 0: # Understocked, increase price
                    adjusted_price = base_price * (
                        1
                        + signed_power * adjustment_factor
                    )
                else: # Overstocked, decrease price
                    adjusted_price = base_price * (
                        1
                        - signed_power * adjustment_factor
                    )
            # ---------------------------------------------

            final_price = max(
                self.config_module.MIN_SELL_PRICE,
                min(self.config_module.MAX_SELL_PRICE, adjusted_price),
            )
            firm.last_prices[item_id] = final_price

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
                    "goods_market",
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
