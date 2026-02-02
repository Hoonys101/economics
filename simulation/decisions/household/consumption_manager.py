from typing import List, Any, Optional, Tuple
import random
from simulation.models import Order
from simulation.decisions.household.api import ConsumptionContext
from simulation.schemas import HouseholdActionVector

class ConsumptionManager:
    """
    Manages consumption logic (Maslow, Utility, Veblen, Hoarding).
    Refactored from AIDrivenHouseholdDecisionEngine.
    """

    def check_survival_override(
        self,
        household: Any,
        config: Any,
        market_snapshot: Any,
        current_time: int,
        logger: Optional[Any]
    ) -> Optional[Tuple[List[Order], HouseholdActionVector]]:
        """
        Phase 2: Survival Override.
        Checks if critical needs exceed threshold and triggers panic buying.
        """
        survival_need = household._bio_state.needs.get('survival', 0)
        emergency_threshold = getattr(config, 'survival_need_emergency_threshold', 0.8)
        if not isinstance(emergency_threshold, (int, float)):
            emergency_threshold = 0.8

        if survival_need > emergency_threshold:
            food_id = getattr(config, 'primary_survival_good_id', 'food')
            if not isinstance(food_id, str):
                food_id = 'food'

            ask_price = None
            if market_snapshot:
                # Handle both dict (legacy) and DTO (new) for market_signals
                signals = getattr(market_snapshot, "market_signals", None)
                if isinstance(signals, dict):
                    # Try to get signal for the specific item from dict
                    signal = signals.get(food_id)
                    if signal:
                        if hasattr(signal, 'best_ask') and signal.best_ask is not None:
                            ask_price = signal.best_ask
                        elif isinstance(signal, dict) and signal.get('best_ask') is not None:
                            ask_price = signal['best_ask']
                elif signals: # Assume it's a DTO if not dict and not None
                    # Access DTO attributes directly or via getattr
                    signal_dto = getattr(signals, food_id, None)
                    if signal_dto and getattr(signal_dto, 'best_ask', None) is not None:
                        ask_price = getattr(signal_dto, 'best_ask')

            # If ask_price was found and is valid
            if ask_price is not None:
                # Affordability Check
                if household._econ_state.assets >= ask_price:
                     premium = getattr(config, 'survival_bid_premium', 0.1)
                     if not isinstance(premium, (int, float)):
                         premium = 0.1
                     bid_price = ask_price * (1 + premium)

                     if logger:
                         logger.warning(
                             f"SURVIVAL_OVERRIDE | Agent {household.id} critical need {survival_need:.2f}. Panic buying {food_id} at {bid_price:.2f}",
                             extra={"agent_id": household.id, "tick": current_time, "tags": ["survival", "override"]}
                         )

                     survival_order = Order(
                         agent_id=household.id,
                         side="BUY",
                         item_id=food_id,
                         quantity=1.0,
                         price_limit=bid_price,
                         market_id=food_id
                     )

                     # Return immediately, skipping other logic
                     # We return a vector with high work aggressiveness as survival instinct implies working hard too
                     return [survival_order], HouseholdActionVector(work_aggressiveness=1.0)
        return None

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
                food_inventory = household._econ_state.inventory.get("basic_food", 0.0)
                target_buffer = getattr(config, "target_food_buffer_quantity", 5.0)
                if food_inventory < target_buffer:
                    continue # Skip consumer_goods if food insecure

            # Phase 15: Utility Saturation for Durables
            if hasattr(household, 'durable_assets'):
                 existing_durables = [a for a in household._econ_state.durable_assets if a['item_id'] == item_id]
                 has_inventory = household._econ_state.inventory.get(item_id, 0.0) >= 1.0

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
                nv = household._bio_state.needs.get(need_type, 0.0)
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
            budget_limit = household._econ_state.assets * config.budget_limit_normal_ratio
            if max_need_value > config.budget_limit_urgent_need:
                budget_limit = household._econ_state.assets * config.budget_limit_urgent_ratio

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
                    Order(
                        agent_id=household.id,
                        side="BUY",
                        item_id=item_id,
                        quantity=final_quantity,
                        price_limit=bid_price,
                        market_id=item_id
                    )

                 )

        return orders
