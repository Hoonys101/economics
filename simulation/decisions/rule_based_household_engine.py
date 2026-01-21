from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
import logging

from simulation.models import Order
from simulation.ai.enums import Tactic, Aggressiveness
from .base_decision_engine import BaseDecisionEngine
from simulation.dtos import DecisionContext

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.dtos import MacroFinancialContext

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
        macro_context: Optional[MacroFinancialContext] = None,
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

        # 0. Wage Recovery (Employed Case)
        if household.is_employed:
             recovery_rate = getattr(self.config_module, "WAGE_RECOVERY_RATE", 0.01)
             household.wage_modifier *= (1.0 + recovery_rate)
             household.wage_modifier = min(1.0, household.wage_modifier)

        # 1. 생존 욕구 충족 (음식 구매)
        if (
            household.needs["survival"]
            >= self.config_module.SURVIVAL_NEED_CONSUMPTION_THRESHOLD
        ):
            # FIX: Use "basic_food" instead of hardcoded "food"
            food_item_id = "basic_food"
            food_in_inventory = household.inventory.get(food_item_id, 0.0)

            if food_in_inventory < self.config_module.HOUSEHOLD_MIN_FOOD_INVENTORY:
                chosen_tactic = Tactic.BUY_BASIC_FOOD
                chosen_aggressiveness = Aggressiveness.AGGRESSIVE # 생존 관련이므로 적극적으로 구매

                # 구매할 음식 수량 결정: 최소 재고를 채우거나, 소비 임계치까지 필요한 양
                needed_quantity = self.config_module.HOUSEHOLD_MIN_FOOD_INVENTORY - food_in_inventory

                # FIX: Access specific market if available, or goods_market if combined
                market_id = food_item_id # OrderBookMarket usually keyed by item_id
                market = markets.get(market_id)

                best_ask = market.get_best_ask(item_id=food_item_id) if market else None

                # Fallback if None
                if best_ask is None or best_ask == 0:
                    best_ask = 5.0 # Reasonable default fallback

                if best_ask > 0:
                    affordable_quantity = household.assets / best_ask
                    quantity_to_buy = min(needed_quantity, affordable_quantity, self.config_module.FOOD_PURCHASE_MAX_PER_TICK)
                    
                    if quantity_to_buy > 0.1:
                        orders.append(
                            Order(
                                household.id,
                                "BUY",
                                food_item_id,
                                quantity_to_buy,
                                best_ask,
                                market_id,
                            )
                        )
                        self.logger.info(
                            f"Household {household.id} buying {quantity_to_buy:.2f} {food_item_id} for survival at {best_ask:.2f}",
                            extra={"tick": current_time, "agent_id": household.id, "tactic": chosen_tactic.name}
                        )

        # 2. 노동 시장 참여 (실업 상태일 경우)
        if not household.is_employed and household.assets < self.config_module.ASSETS_THRESHOLD_FOR_OTHER_ACTIONS:
            # 생존 욕구가 높거나 자산이 부족하면 노동 시장에 참여
            if chosen_tactic == Tactic.NO_ACTION: # 음식 구매가 이미 결정되었으면 이번 턴에는 노동 시장 참여 안함 (간단화를 위해)
                chosen_tactic = Tactic.PARTICIPATE_LABOR_MARKET
                chosen_aggressiveness = Aggressiveness.NEUTRAL # 규칙 기반은 공격성 중립으로 설정

                # --- Phase 21.6: Adaptive Wage Logic & Survival Override ---

                # 1. Update Wage Modifier (Adaptive)
                decay_rate = getattr(self.config_module, "WAGE_DECAY_RATE", 0.02)
                floor_mod = getattr(self.config_module, "RESERVATION_WAGE_FLOOR", 0.3)
                household.wage_modifier *= (1.0 - decay_rate)
                household.wage_modifier = max(floor_mod, household.wage_modifier)
                
                # 2. Survival Trigger (Panic Mode)
                food_inventory = household.inventory.get("basic_food", 0.0)
                food_price = market_data.get("goods_market", {}).get("basic_food_avg_traded_price", 10.0)
                if food_price <= 0: food_price = 10.0

                survival_days = food_inventory + (household.assets / food_price)
                critical_turns = getattr(self.config_module, "SURVIVAL_CRITICAL_TURNS", 5)

                is_panic = False
                desired_wage = 0.0

                if survival_days < critical_turns:
                    is_panic = True
                    desired_wage = 0.0
                    self.logger.info(
                        f"PANIC_MODE | Household {household.id} desperate (RuleBased). Survival Days: {survival_days:.1f}. Wage: 0.0",
                        extra={"tick": current_time, "agent_id": household.id, "tags": ["labor_panic"]}
                    )
                else:
                    # Normal Adaptive Wage
                    labor_market_info = market_data.get("goods_market", {}).get("labor", {})
                    market_avg_wage = labor_market_info.get("avg_wage", self.config_module.LABOR_MARKET_MIN_WAGE)
                    desired_wage = market_avg_wage * household.wage_modifier

                # 3. Generate Order
                # Retrieve Market Data
                labor_market_info = market_data.get("goods_market", {}).get("labor", {})
                market_avg_wage = labor_market_info.get("avg_wage", self.config_module.LABOR_MARKET_MIN_WAGE)
                best_market_offer = labor_market_info.get("best_wage_offer", 0.0)

                # Refuse labor supply if market offer is too low (only if NOT panic)
                effective_offer = best_market_offer if best_market_offer > 0 else market_avg_wage
                # [Fix] Use dynamic reservation_wage as floor, not fixed 0.7 ratio
                # wage_floor = market_avg_wage * getattr(self.config_module, "RESERVATION_WAGE_FLOOR_RATIO", 0.7)
                wage_floor = desired_wage

                if not is_panic and effective_offer < wage_floor:
                    self.logger.info(
                        f"RESERVATION_WAGE | Household {household.id} refused labor (RuleBased). "
                        f"Offer: {effective_offer:.2f} < Floor: {wage_floor:.2f} (Avg: {market_avg_wage:.2f}, Mod: {household.wage_modifier:.2f})",
                        extra={"tick": current_time, "agent_id": household.id, "tags": ["labor_refusal"]}
                    )
                    # Skip order generation
                else:
                    orders.append(
                        Order(
                            household.id,
                            "SELL",
                            "labor",
                            1.0,  # 1 unit of labor
                            desired_wage,
                            "labor", # FIX: Use correct market ID "labor"
                        )
                    )
                    self.logger.info(
                        f"Household {household.id} offers labor at wage {desired_wage:.2f}",
                        extra={"tick": current_time, "agent_id": household.id, "tactic": chosen_tactic.name}
                    )

        # TODO: 다른 규칙 기반 로직 (예: 저축, 투자, 사치품 구매 등) 추가
        
        return orders, (chosen_tactic, chosen_aggressiveness)
