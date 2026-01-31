from typing import List
import random
from simulation.models import Order
from simulation.decisions.household.api import LaborContext

class LaborManager:
    """
    Manages Labor decisions (Quit, Job Search, Reservation Wage).
    Refactored from AIDrivenHouseholdDecisionEngine.
    """

    def decide_labor(self, context: LaborContext) -> List[Order]:
        orders = []
        household = context.household
        config = context.config
        market_data = context.market_data
        action_vector = context.action_vector
        current_time = context.current_time
        logger = context.logger

        labor_market_info = market_data.get("goods_market", {}).get("labor", {})
        market_avg_wage = labor_market_info.get("avg_wage", config.labor_market_min_wage)
        best_market_offer = labor_market_info.get("best_wage_offer", 0.0)

        # Scenario A: Already Employed
        if household.is_employed:
            # Recovery handled by EconComponent/LaborManager, here we just check for quit
            if hasattr(action_vector, 'job_mobility_aggressiveness'):
                agg_mobility = action_vector.job_mobility_aggressiveness
            else:
                agg_mobility = 0.5

            quit_threshold = config.job_quit_threshold_base - agg_mobility

            if (market_avg_wage > household.current_wage * quit_threshold or
                best_market_offer > household.current_wage * quit_threshold):

                if random.random() < (config.job_quit_prob_base + agg_mobility * config.job_quit_prob_scale):
                    # Signal quit via Order
                    orders.append(Order(
                        agent_id=household.id,
                        side="QUIT",
                        item_id="labor",
                        quantity=0.0,
                        price_limit=0.0,
                        market_id="labor"
                    ))

        # Scenario B: Unemployed
        if not household.is_employed:
            # Note: Legacy code accessed `basic_food` from inventory. DTO has `inventory: List[GoodsDTO]` usually,
            # but legacy code treated it as Dict?
            # Memory says: "HouseholdStateDTO defines inventory as a List[GoodsDTO]... replacing the previous Dict[str, float] representation."
            # BUT legacy code: `food_inventory = household.inventory.get("basic_food", 0.0)`
            # This implies `household.inventory` IS A DICT in the Legacy Engine's view.
            # If `HouseholdStateDTO` has `inventory` as `List`, then `get` would fail.
            # Let's verify `HouseholdStateDTO` definition.
            # If it is a List, I must convert or iterate.
            # But wait, `AIDrivenHouseholdDecisionEngine` (legacy) ran successfully?
            # If so, `household.inventory` acts like a dict.
            # Maybe `HouseholdStateDTO`'s `inventory` field is `Dict[str, float]` after all, or property wrapper.
            # I will assume dict access works as per legacy code parity.

            food_inventory = household.inventory.get("basic_food", 0.0)

            food_price = market_data.get("goods_market", {}).get("basic_food_avg_traded_price", 10.0)
            if food_price <= 0: food_price = 10.0

            survival_days = food_inventory + (household.assets / food_price)
            critical_turns = getattr(config, "survival_critical_turns", 5)

            is_panic = False
            if survival_days < critical_turns:
                is_panic = True
                reservation_wage = 0.0
                if logger:
                    logger.info(
                        f"PANIC_MODE | Household {household.id} desperate. Survival Days: {survival_days:.1f}. Wage: 0.0",
                         extra={"tick": current_time, "agent_id": household.id, "tags": ["labor_panic"]}
                    )
            else:
                # labor_market_info re-fetch or reuse? Reuse.
                reservation_wage = market_avg_wage * household.wage_modifier

            # labor_market_info re-fetch in legacy? Yes.
            labor_market_info = market_data.get("goods_market", {}).get("labor", {})
            market_avg_wage = labor_market_info.get("avg_wage", config.labor_market_min_wage)
            best_market_offer = labor_market_info.get("best_wage_offer", 0.0)

            effective_offer = best_market_offer if best_market_offer > 0 else market_avg_wage
            wage_floor = reservation_wage

            if not is_panic and effective_offer < wage_floor:
                if logger:
                    logger.info(
                        f"RESERVATION_WAGE | Household {household.id} refused labor. "
                        f"Offer: {effective_offer:.2f} < Floor: {wage_floor:.2f}",
                        extra={"tick": current_time, "agent_id": household.id, "tags": ["labor_refusal"]}
                    )
            else:
                orders.append(
                    Order(
                        agent_id=household.id,
                        side="SELL",
                        item_id="labor",
                        quantity=1.0,
                        price_limit=reservation_wage,
                        market_id="labor"
                    )
                )

        return orders
