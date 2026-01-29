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


            # --- Organic Substitution Effect: Saving vs Consumption ROI ---
            avg_price = market_data.get("goods_market", {}).get(f"{item_id}_current_sell_price", config.market_price_fallback)
            if not avg_price or avg_price <= 0:
                avg_price = config.market_price_fallback

            good_info = config.goods.get(item_id, {})
            is_luxury = good_info.get("is_luxury", False)

            # Need Value (UC)
            max_need_value = 0.0
            utility_effects = good_info.get("utility_effects", {})
            for need_type in utility_effects.keys():
                nv = household.needs.get(need_type, 0.0)
                if nv > max_need_value:
                    max_need_value = nv

            # --- 3-Pillars ROI Calculation ---
            preference_weight = household.preference_social if is_luxury else household.preference_growth
            consumption_roi = (max_need_value / (avg_price + 1e-9)) * preference_weight

            # If Saving is more attractive, attenuate aggressiveness
            if savings_roi > consumption_roi:
                attenuation = consumption_roi / (savings_roi + 1e-9)
                if max_need_value > 40:
                    attenuation = max(0.5, attenuation)
                else:
                    attenuation = max(0.1, attenuation)
                agg_buy *= attenuation

            if random.random() < 0.05:
                if logger:
                    logger.info(
                        f"MONETARY_TRANS | HH {household.id} | {item_id} | Need: {max_need_value:.1f} | "
                        f"ConsROI: {consumption_roi:.2f} vs SavROI: {savings_roi:.4f} | AggBuy: {agg_buy:.2f}"
                    )

            agg_buy *= debt_penalty
            agg_buy = max(0.0, agg_buy)

            if random.random() < 0.001:
                if logger:
                    logger.debug(
                        f"MONETARY_TRANS | Agent {household.id} {item_id}: "
                        f"SavROI: {savings_roi:.4f} vs ConsROI: {consumption_roi:.4f} -> Agg: {agg_buy:.2f}"
                    )

            # Recalculate need_factor and valuation (Parity with Legacy)
            # Legacy code re-gets avg_price and max_need_value here.
            # It seems redundant but to ensure strict parity I should check if anything changed or if it was just bad coding.
            # It seems just re-fetching.

            avg_price = market_data.get("goods_market", {}).get(f"{item_id}_current_sell_price", config.market_price_fallback)
            if not avg_price or avg_price <= 0:
                avg_price = config.market_price_fallback

            max_need_value = 0.0
            for need_type in utility_effects.keys():
                nv = household.needs.get(need_type, 0.0)
                if nv > max_need_value:
                    max_need_value = nv

            need_factor = config.need_factor_base + (max_need_value / config.need_factor_scale)
            valuation_modifier = config.valuation_modifier_base + (agg_buy * config.valuation_modifier_range)

            willingness_to_pay = avg_price * need_factor * valuation_modifier

            # --- Phase 17-4: Veblen Demand Effect ---
            if getattr(config, "enable_vanity_system", False) and good_info.get("is_veblen", False):
                conformity = getattr(household, "conformity", 0.5)
                prestige_boost = avg_price * 0.1 * conformity
                willingness_to_pay += prestige_boost
                agg_buy = min(1.0, agg_buy * (1.0 + 0.2 * conformity))

            # 3. Execution: Multi-unit Purchase Logic (Bulk Buying)
            max_q = config.household_max_purchase_quantity
            target_quantity = 1.0

            if max_need_value > config.bulk_buy_need_threshold:
                target_quantity = max_q
            elif agg_buy > config.bulk_buy_agg_threshold:
                target_quantity = max(1.0, max_q * config.bulk_buy_moderate_ratio)

            # --- Phase 8: Inflation Psychology (Hoarding & Delay) ---
            expected_inflation = household.expected_inflation.get(item_id, 0.0)

            if expected_inflation > getattr(config, "panic_buying_threshold", 0.05):
                hoarding_factor = getattr(config, "hoarding_factor", 0.5)
                target_quantity *= (1.0 + hoarding_factor)
                willingness_to_pay *= (1.0 + expected_inflation)

            elif expected_inflation < getattr(config, "deflation_wait_threshold", -0.05):
                delay_factor = getattr(config, "delay_factor", 0.5)
                target_quantity *= (1.0 - delay_factor)
                willingness_to_pay *= (1.0 + expected_inflation)

            # Phase 28: Stress Scenario - Hoarding
            if stress_config and stress_config.is_active and stress_config.scenario_name == 'hyperinflation':
                consumables = getattr(config, "household_consumable_goods", ["basic_food", "luxury_food"])
                if item_id in consumables:
                     target_quantity *= (1.0 + stress_config.hoarding_propensity_factor)
                     willingness_to_pay *= (1.0 + stress_config.hoarding_propensity_factor * 0.5)
                     if random.random() < 0.05 and logger:
                         logger.info(f"HOARDING_TRIGGER | Household {household.id} hoarding {item_id} (x{target_quantity:.1f})")

            budget_limit = household.assets * config.budget_limit_normal_ratio
            if max_need_value > config.budget_limit_urgent_need:
                budget_limit = household.assets * config.budget_limit_urgent_ratio

            if willingness_to_pay * target_quantity > budget_limit:
                target_quantity = budget_limit / willingness_to_pay

            if target_quantity >= config.min_purchase_quantity and willingness_to_pay > 0:
                final_quantity = target_quantity
                if good_info.get("is_durable", False):
                    final_quantity = max(1, int(target_quantity))

                orders.append(
                    Order(household.id, "BUY", item_id, final_quantity, willingness_to_pay, item_id)
                )

        return orders
