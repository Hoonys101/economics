from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
import logging

from simulation.models import Order
from simulation.ai.enums import Tactic, Aggressiveness
from .rule_based_firm_engine import RuleBasedFirmDecisionEngine
from .base_decision_engine import BaseDecisionEngine

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
        firm: Firm,
        markets: Dict[str, Any],
        goods_data: List[Dict[str, Any]],
        market_data: Dict[str, Any],
        current_time: int,
    ) -> Tuple[List[Order], Tuple[Tactic, Aggressiveness]]:
        """
        AI 엔진을 사용하여 최적의 전술을 결정하고, 그에 따른 주문을 생성한다.
        """
        agent_data = firm.get_agent_data()
        pre_state_data = firm.get_pre_state_data()

        # AI에게 전술 결정 위임
        chosen_tactic_tuple = self.ai_engine.decide_and_learn(
            agent_data, market_data, pre_state_data
        )
        tactic, aggressiveness = chosen_tactic_tuple

        # 전술에 따른 실행
        orders = self._execute_tactic(tactic, aggressiveness, firm, current_time, market_data)

        return orders, chosen_tactic_tuple

    def _execute_tactic(
        self, tactic: Tactic, aggressiveness: Aggressiveness, firm: Firm, current_tick: int, market_data: Dict[str, Any]
    ) -> List[Order]:
        """
        선택된 전술에 따라 실제 행동(주문 생성)을 수행한다.
        가격 관련 전술은 직접 처리하고, 나머지는 규칙 기반 엔진에 위임한다.
        """
        self.logger.info(
            f"Firm {firm.id} chose Tactic: {tactic.name} with Aggressiveness: {aggressiveness.name}",
            extra={"tick": current_tick, "agent_id": firm.id, "tactic": tactic.name, "aggressiveness": aggressiveness.name},
        )

        if tactic in [
            Tactic.PRICE_INCREASE_SMALL,
            Tactic.PRICE_DECREASE_SMALL,
            Tactic.PRICE_INCREASE_MEDIUM,
            Tactic.PRICE_DECREASE_MEDIUM,
            Tactic.PRICE_HOLD,
        ]:
            return self._adjust_price_with_ai(firm, current_tick, tactic)
        elif tactic == Tactic.ADJUST_PRODUCTION:
            return self.rule_based_engine._adjust_production(firm, current_tick)
        elif tactic == Tactic.ADJUST_WAGES:
            return self.rule_based_engine._adjust_wages(firm, current_tick, market_data)
        elif tactic == Tactic.ADJUST_PRICE:
            return self._adjust_price(firm, current_tick)

        return []

    def _adjust_price(self, firm: Firm, current_tick: int) -> List[Order]:
        """
        재고 수준에 따라 판매 가격을 조정하고 판매 주문을 생성한다.
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

            if not is_understocked:
                base_price = firm.last_prices.get(
                    item_id, self.config_module.GOODS[item_id]["production_cost"]
                )

                adjusted_price = base_price
                if target_inventory > 0:
                    diff_ratio = (
                        current_inventory - target_inventory
                    ) / target_inventory
                    signed_power = (
                        abs(diff_ratio) ** self.config_module.PRICE_ADJUSTMENT_EXPONENT
                    )
                    if diff_ratio < 0:
                        adjusted_price = base_price * (
                            1
                            + signed_power * self.config_module.PRICE_ADJUSTMENT_FACTOR
                        )
                    else:
                        adjusted_price = base_price * (
                            1
                            - signed_power * self.config_module.PRICE_ADJUSTMENT_FACTOR
                        )

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
                        f"Planning to SELL {quantity_to_sell:.1f} of {item_id} at price {final_price:.2f}",
                        extra={
                            "tick": current_tick,
                            "agent_id": firm.id,
                            "tags": ["sell_order"],
                        },
                    )

        return orders

    def _adjust_price_with_ai(
        self, firm: Firm, current_tick: int, tactic: Tactic
    ) -> List[Order]:
        """
        AI가 결정한 가격 조정 전술에 따라 판매 가격을 조정하고 판매 주문을 생성한다.
        """
        orders = []
        item_id = firm.specialization
        current_inventory = firm.inventory.get(item_id, 0)

        if current_inventory > 0:
            base_price = firm.last_prices.get(
                item_id, self.config_module.GOODS[item_id]["production_cost"]
            )

            adjustment_map = {
                Tactic.PRICE_INCREASE_SMALL: self.config_module.AI_PRICE_ADJUSTMENT_SMALL,
                Tactic.PRICE_INCREASE_MEDIUM: self.config_module.AI_PRICE_ADJUSTMENT_MEDIUM,
                Tactic.PRICE_DECREASE_SMALL: -self.config_module.AI_PRICE_ADJUSTMENT_SMALL,
                Tactic.PRICE_DECREASE_MEDIUM: -self.config_module.AI_PRICE_ADJUSTMENT_MEDIUM,
                Tactic.PRICE_HOLD: 0,
            }

            adjustment_factor = adjustment_map.get(tactic, 0)
            adjusted_price = base_price * (1 + adjustment_factor)

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
                    f"AI Tactic {tactic.name}: Planning to SELL {quantity_to_sell:.1f} of {item_id} at price {final_price:.2f}",
                    extra={
                        "tick": current_tick,
                        "agent_id": firm.id,
                        "tags": ["sell_order", "ai_tactic"],
                    },
                )
        return orders
