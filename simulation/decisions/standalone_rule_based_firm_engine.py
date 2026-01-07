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

        # 2. 임금 조정 및 고용 결정 (생산 조정 이후 필요에 따라)
        # 현재 생산 목표와 실제 생산량, 고용 인원 등을 고려하여 임금 및 고용 결정 로직 추가
        if chosen_tactic != Tactic.ADJUST_PRODUCTION: # 이미 생산 조정 결정을 했으면 이번 턴에 임금 조정은 건너뛴다 (간단화를 위해)
            needed_labor_for_production = self.rule_based_executor._calculate_needed_labor(firm)
            if len(firm.employees) < needed_labor_for_production * self.config_module.FIRM_LABOR_REQUIREMENT_RATIO or \
               len(firm.employees) < self.config_module.FIRM_MIN_EMPLOYEES:
                chosen_tactic = Tactic.ADJUST_WAGES # ADJUST_WAGES 전술에 고용 로직도 포함되어 있음
                orders.extend(self.rule_based_executor._adjust_wages(firm, current_time, market_data))
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
                0.1, # Absolute hard floor to prevent zero/negative
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
