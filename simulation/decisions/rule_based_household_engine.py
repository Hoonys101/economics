from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
import logging

from simulation.models import Order
from simulation.ai.enums import Tactic, Aggressiveness
from .base_decision_engine import BaseDecisionEngine
from simulation.dtos import DecisionContext

if TYPE_CHECKING:
    from simulation.core_agents import Household

logger = logging.getLogger(__name__)


class RuleBasedHouseholdDecisionEngine(BaseDecisionEngine):
    """
    가계의 규칙 기반 의사결정을 담당하는 엔진.
    AI가 없는 환경에서 가계의 기본적인 경제 활동을 시뮬레이션한다.
    """

    def __init__(
        self, config_module: Any, logger: Optional[logging.Logger] = None
    ) -> None:
        self.config_module = config_module
        self.logger = logger if logger else logging.getLogger(__name__)
        self.logger.info(
            "RuleBasedHouseholdDecisionEngine initialized.",
            extra={"tick": 0, "tags": ["init"]},
        )

    def make_decisions(
        self,
        context: DecisionContext,
    ) -> Tuple[List[Order], Tuple[Tactic, Aggressiveness]]:
        """
        규칙 기반 로직을 사용하여 가계의 의사결정을 수행한다.
        주로 생존 욕구 충족과 노동 시장 참여에 집중한다.
        """
        household = context.household
        markets = context.markets
        goods_data = context.goods_data
        market_data = context.market_data
        current_time = context.current_time

        if household is None:
            return [], (Tactic.NO_ACTION, Aggressiveness.NEUTRAL)

        orders: List[Order] = []
        chosen_tactic: Tactic = Tactic.NO_ACTION
        chosen_aggressiveness: Aggressiveness = Aggressiveness.NEUTRAL

        # 1. 생존 욕구 충족 (음식 구매)
        if (
            household.needs["survival"]
            >= self.config_module.SURVIVAL_NEED_CONSUMPTION_THRESHOLD
        ):
            food_in_inventory = household.inventory.get("food", 0.0)
            if food_in_inventory < self.config_module.HOUSEHOLD_MIN_FOOD_INVENTORY:
                chosen_tactic = Tactic.BUY_BASIC_FOOD
                chosen_aggressiveness = Aggressiveness.AGGRESSIVE # 생존 관련이므로 적극적으로 구매

                # 구매할 음식 수량 결정: 최소 재고를 채우거나, 소비 임계치까지 필요한 양
                needed_quantity = self.config_module.HOUSEHOLD_MIN_FOOD_INVENTORY - food_in_inventory
                market = markets.get("goods_market")

                best_ask = market.get_best_ask(item_id="food") if market else None
                if best_ask and best_ask > 0:
                    affordable_quantity = household.assets / best_ask
                    quantity_to_buy = min(needed_quantity, affordable_quantity, self.config_module.FOOD_PURCHASE_MAX_PER_TICK)
                    
                    if quantity_to_buy > 0:
                        orders.append(
                            Order(
                                household.id,
                                "BUY",
                                "food",
                                quantity_to_buy,
                                best_ask,
                                "goods_market",
                            )
                        )
                        self.logger.info(
                            f"Household {household.id} buying {quantity_to_buy:.2f} food for survival at {best_ask:.2f}",
                            extra={"tick": current_time, "agent_id": household.id, "tactic": chosen_tactic.name}
                        )

        # 2. 노동 시장 참여 (실업 상태일 경우)
        if not household.is_employed and household.assets < self.config_module.ASSETS_THRESHOLD_FOR_OTHER_ACTIONS:
            # 생존 욕구가 높거나 자산이 부족하면 노동 시장에 참여
            if chosen_tactic == Tactic.NO_ACTION: # 음식 구매가 이미 결정되었으면 이번 턴에는 노동 시장 참여 안함 (간단화를 위해)
                chosen_tactic = Tactic.PARTICIPATE_LABOR_MARKET
                chosen_aggressiveness = Aggressiveness.NEUTRAL # 규칙 기반은 공격성 중립으로 설정

                desired_wage = household.get_desired_wage()

                # --- Genesis: Wage Surrender Logic (WO-Diag-005) ---
                # If survival need is critical, aggressively lower wage demand.
                if household.needs["survival"] >= self.config_module.SURVIVAL_NEED_THRESHOLD:
                    base_wage = desired_wage
                    desired_wage = max(1.0, base_wage * self.config_module.GENESIS_WAGE_FLEXIBILITY_FACTOR)

                    self.logger.warning(
                        f"WAGE_SURRENDER | Household {household.id} is desperate (Survival: {household.needs['survival']:.1f}). Dropping wage: {base_wage:.2f} -> {desired_wage:.2f}",
                        extra={"tick": current_time, "agent_id": household.id, "tags": ["wage_surrender"]}
                    )
                # ---------------------------------------------------

                orders.append(
                    Order(
                        household.id,
                        "SELL",
                        "labor",
                        1.0,  # 1 unit of labor
                        desired_wage,
                        "labor_market",
                    )
                )
                self.logger.info(
                    f"Household {household.id} offers labor at wage {desired_wage:.2f}",
                    extra={"tick": current_time, "agent_id": household.id, "tactic": chosen_tactic.name}
                )

        # TODO: 다른 규칙 기반 로직 (예: 저축, 투자, 사치품 구매 등) 추가
        
        return orders, (chosen_tactic, chosen_aggressiveness)
