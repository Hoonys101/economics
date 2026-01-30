from typing import List, Any, Optional
import random
from simulation.models import Order
from simulation.decisions.household.api import ConsumptionContext

class ConsumptionManager:
    """
    Manages consumption logic (Maslow, Utility, Veblen, Hoarding).
    Refactored from AIDrivenHouseholdDecisionEngine.
    """

    def decide_consumption(self, context: ConsumptionContext) -> List[Order]:
        orders = []
        household = context.household
        config = context.config
        market_data = context.market_data
        action_vector = context.action_vector
        savings_roi = context.savings_roi
        debt_penalty = context.debt_penalty
        stress_config = context.stress_config
        logger = context.logger

        goods_list = list(config.goods.keys())

        # 2. Execution: Consumption Logic (Per Item)
        for item_id in goods_list:
            # WO-023: Maslow Constraint (Food Security First)
            if item_id == "consumer_goods":
                food_inventory = household.inventory.get("basic_food", 0.0)
                target_buffer = getattr(config, "target_food_buffer_quantity", 5.0)
                if food_inventory < target_buffer:
                    continue # Skip consumer_goods if food insecure

            # Phase 15: Utility Saturation for Durables
            if hasattr(household, 'durable_assets'):
                 existing_durables = [a for a in household.durable_assets if a['item_id'] == item_id]
                 has_inventory = household.inventory.get(item_id, 0.0) >= 1.0

                 if existing_durables or has_inventory:
                     if random.random() < 0.95: # 95% chance to skip
                         continue

            # Check action_vector type and access
            # action_vector is likely HouseholdActionVector object
            if hasattr(action_vector, 'consumption_aggressiveness'):
                 agg_buy = action_vector.consumption_aggressiveness.get(item_id, 0.5)
            else:
                 agg_buy = 0.5


            # --- WO-157: Continuous Demand Curve Implementation ---
            avg_price = market_data.get("goods_market", {}).get(f"{item_id}_current_sell_price", config.market_price_fallback)
            if not avg_price or avg_price <= 0:
                avg_price = config.market_price_fallback

            good_info = config.goods.get(item_id, {})

            # 1. Need Urgency (Demand Ceiling)
            max_need_value = 0.0
            utility_effects = good_info.get("utility_effects", {})
            for need_type in utility_effects.keys():
                nv = household.needs.get(need_type, 0.0)
                if nv > max_need_value:
                    max_need_value = nv

            # 2. Demand Elasticity & WTP Multiplier
            demand_elasticity = getattr(household, 'demand_elasticity', 1.0)
            mwtp_multiplier = getattr(config, 'max_willingness_to_pay_multiplier', 2.5)

            # 3. Max Affordable Price (Reservation Price)
            # Use perceived price as baseline for WTP calculation
            perceived_price = household.perceived_prices.get(item_id, avg_price)
            max_affordable_price = mwtp_multiplier * perceived_price

            quantity_to_buy = 0.0

            # 4. Demand Curve Calculation
            if avg_price >= max_affordable_price:
                 quantity_to_buy = 0.0
            else:
                 price_ratio = avg_price / max_affordable_price
                 # Q = Urgency * (1 - P/P_max)^Elasticity
                 quantity_to_buy = max_need_value * ((1.0 - price_ratio) ** demand_elasticity)

            # --- Phase 17-4: Veblen Demand Effect (Integrated) ---
            # Veblen goods have inverted or reduced elasticity for status seekers, but here we model it
            # as a boost to quantity or WTP.
            if getattr(config, "enable_vanity_system", False) and good_info.get("is_veblen", False):
                conformity = getattr(household, "conformity", 0.5)
                # Boost Max Affordable Price (willing to pay more)
                max_affordable_price *= (1.0 + 0.5 * conformity)
                # Re-calculate with boosted WTP
                if avg_price < max_affordable_price:
                    price_ratio = avg_price / max_affordable_price
                    quantity_to_buy = max_need_value * ((1.0 - price_ratio) ** demand_elasticity)
                    # Status boost to quantity
                    quantity_to_buy *= (1.0 + 0.2 * conformity)

            # 5. Budget Constraint (Zero-Sum Integrity)
            budget_limit = household.assets * config.budget_limit_normal_ratio
            if max_need_value > config.budget_limit_urgent_need:
                budget_limit = household.assets * config.budget_limit_urgent_ratio

            # Determine Bid Price First
            # WO-157: Bid slightly above avg_price to ensure execution if urgent, capped at max_affordable_price.
            bid_price = avg_price * 1.05
            if bid_price > max_affordable_price:
                bid_price = max_affordable_price
            # Ensure we don't bid below avg_price if we want to buy
            bid_price = max(bid_price, avg_price)

            # Apply Budget Constraint using actual Bid Price
            cost = quantity_to_buy * bid_price
            if cost > budget_limit:
                 quantity_to_buy = budget_limit / bid_price

            # Threshold and Order Generation
            if quantity_to_buy >= config.min_purchase_quantity:
                 final_quantity = quantity_to_buy
                 if good_info.get("is_durable", False):
                     final_quantity = max(1, int(quantity_to_buy))

                 orders.append(
                    Order(household.id, "BUY", item_id, final_quantity, bid_price, item_id)
                 )

        return orders
