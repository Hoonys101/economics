from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
import logging

from simulation.models import Order
from simulation.ai.enums import Tactic, Aggressiveness
from .base_decision_engine import BaseDecisionEngine
from simulation.dtos import DecisionContext, DecisionOutputDTO

if TYPE_CHECKING:
    from simulation.dtos import MacroFinancialContext
    from modules.household.dtos import HouseholdStateDTO
    from simulation.dtos import HouseholdConfigDTO

logger = logging.getLogger(__name__)


class RuleBasedHouseholdDecisionEngine(BaseDecisionEngine):
    """
    가계의 규칙 기반 의사결정을 담당하는 엔진.
    AI가 없는 환경에서 가계의 기본적인 경제 활동을 시뮬레이션한다.
    Pure Function: Only uses DecisionContext.state and DecisionContext.config.
    """

    def __init__(
        self, config_module: Any, logger: Optional[logging.Logger] = None
    ) -> None:
        self.config_module = config_module
        self.logger = logger if logger else logging.getLogger(__name__)
        self.logger.info(
            "RuleBasedHouseholdDecisionEngine initialized (Pure).",
            extra={"tick": 0, "tags": ["init"]},
        )

    def _make_decisions_internal(
        self,
        context: DecisionContext,
        macro_context: Optional[MacroFinancialContext] = None,
    ) -> DecisionOutputDTO:
        """
        규칙 기반 로직을 사용하여 가계의 의사결정을 수행한다.
        """
        state: HouseholdStateDTO = context.state
        config: HouseholdConfigDTO = context.config
        
        # TD-117: Use DTOs
        market_snapshot = context.market_snapshot
        market_data = context.market_data
        current_time = context.current_time

        orders: List[Order] = []
        chosen_tactic: Tactic = Tactic.NO_ACTION
        chosen_aggressiveness: Aggressiveness = Aggressiveness.NEUTRAL

        # 1. 생존 욕구 충족 (음식 구매)
        if (
            state.needs["survival"]
            >= config.survival_need_consumption_threshold
        ):
            food_item_id = "basic_food"
            food_in_inventory = state.inventory.get(food_item_id, 0.0)
            target_buffer = config.target_food_buffer_quantity

            if food_in_inventory < target_buffer:
                chosen_tactic = Tactic.BUY_BASIC_FOOD
                chosen_aggressiveness = Aggressiveness.AGGRESSIVE 

                needed_quantity = target_buffer - food_in_inventory
                market_id = food_item_id 

                # TD-117: Use MarketSnapshotDTO (Standardized)
                best_ask = None
                if market_snapshot and market_snapshot.market_signals:
                    signal = market_snapshot.market_signals.get(food_item_id)
                    if signal:
                        best_ask = signal.best_ask

                if best_ask is None or best_ask == 0:
                    best_ask = getattr(self.config_module, "DEFAULT_FALLBACK_PRICE", 5.0)

                if best_ask > 0:
                    affordable_quantity = state.assets / best_ask
                    quantity_to_buy = min(needed_quantity, affordable_quantity, config.food_purchase_max_per_tick)
                    
                    if quantity_to_buy > 0.1:
                        orders.append(
                            Order(
                                agent_id=state.id,
                                side="BUY",
                                item_id=food_item_id,
                                quantity=quantity_to_buy,
                                price_limit=best_ask,
                                market_id=market_id,
                            )
                        )
                        self.logger.info(
                            f"Household {state.id} buying {quantity_to_buy:.2f} {food_item_id} for survival at {best_ask:.2f}",
                            extra={"tick": current_time, "agent_id": state.id, "tactic": chosen_tactic.name}
                        )

        # 2. 노동 시장 참여 (실업 상태일 경우)
        if not state.is_employed and state.assets < config.assets_threshold_for_other_actions:
            if chosen_tactic == Tactic.NO_ACTION:
                chosen_tactic = Tactic.PARTICIPATE_LABOR_MARKET
                chosen_aggressiveness = Aggressiveness.NEUTRAL

            # 2. Survival Trigger (Panic Mode)
            food_inventory = state.inventory.get("basic_food", 0.0)

            # Use market_snapshot for price if available, else fallback
            food_price = 10.0
            if market_snapshot and market_snapshot.market_signals:
                 signal = market_snapshot.market_signals.get("basic_food")
                 if signal and signal.last_traded_price:
                     food_price = signal.last_traded_price
                 elif signal and signal.best_ask:
                     food_price = signal.best_ask

            if food_price <= 0:
                food_price = market_data.get("goods_market", {}).get("basic_food_avg_traded_price", 10.0)

            if food_price <= 0: food_price = 10.0

            survival_days = food_inventory + (state.assets / food_price)
            critical_turns = config.survival_critical_turns

            is_panic = False
            desired_wage = 0.0

            if survival_days < critical_turns:
                is_panic = True
                desired_wage = 0.0
                self.logger.info(
                    f"PANIC_MODE_PURE | Household {state.id} desperate. Survival Days: {survival_days:.1f}. Wage: 0.0",
                    extra={"tick": current_time, "agent_id": state.id, "tags": ["labor_panic"]}
                )
            else:
                labor_market_info = market_data.get("goods_market", {}).get("labor", {})
                market_avg_wage = labor_market_info.get("avg_wage", config.labor_market_min_wage)
                desired_wage = market_avg_wage * state.wage_modifier

            labor_market_info = market_data.get("goods_market", {}).get("labor", {})
            market_avg_wage = labor_market_info.get("avg_wage", config.labor_market_min_wage)
            best_market_offer = labor_market_info.get("best_wage_offer", 0.0)

            effective_offer = best_market_offer if best_market_offer > 0 else market_avg_wage
            wage_floor = desired_wage

            if not is_panic and effective_offer < wage_floor:
                self.logger.info(
                    f"RESERVATION_WAGE_PURE | Household {state.id} refused labor. "
                    f"Offer: {effective_offer:.2f} < Floor: {wage_floor:.2f}",
                    extra={"tick": current_time, "agent_id": state.id, "tags": ["labor_refusal"]}
                )
            else:
                orders.append(
                    Order(
                        agent_id=state.id,
                        side="SELL",
                        item_id="labor",
                        quantity=1.0,  # 1 unit of labor
                        price_limit=desired_wage,
                        market_id="labor",
                    )
                )
                self.logger.info(
                    f"Household {state.id} offers labor at wage {desired_wage:.2f}",
                    extra={"tick": current_time, "agent_id": state.id, "tactic": chosen_tactic.name}
                )

        return DecisionOutputDTO(orders=orders, metadata=(chosen_tactic, chosen_aggressiveness))
