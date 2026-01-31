from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from modules.household.api import IConsumptionManager
from modules.household.dtos import EconStateDTO
from simulation.dtos import ConsumptionResult
from simulation.dtos.config_dtos import HouseholdConfigDTO

class ConsumptionManager(IConsumptionManager):
    """
    Stateless manager responsible for consumption logic.
    """

    def consume(
        self,
        state: EconStateDTO,
        needs: Dict[str, float],
        item_id: str,
        quantity: float,
        current_time: int,
        goods_info: Dict[str, Any],
        config: HouseholdConfigDTO
    ) -> Tuple[EconStateDTO, Dict[str, float], ConsumptionResult]:
        """
        Consumes an item, updating inventory, consumption tracking, and needs.
        Logic migrated from EconComponent.consume.
        """
        new_state = state.copy()
        new_needs = needs.copy()

        is_service = goods_info.get("is_service", False)
        inventory_qty = new_state.inventory.get(item_id, 0.0)

        if is_service or inventory_qty >= quantity:
            if not is_service:
                new_state.inventory[item_id] = max(0.0, inventory_qty - quantity)

            # Durable goods logic
            is_durable = goods_info.get("is_durable", False)
            if is_durable and not is_service:
                base_lifespan = goods_info.get("base_lifespan", 50)
                quality = new_state.inventory_quality.get(item_id, 1.0)
                num_assets = int(round(quantity))
                for _ in range(num_assets):
                    asset = {
                        "item_id": item_id,
                        "quality": quality,
                        "remaining_life": base_lifespan,
                    }
                    new_state.durable_assets.append(asset)

            # Education XP logic
            if item_id == "education_service":
                learning_efficiency = config.learning_efficiency
                xp_gain = quantity * learning_efficiency
                new_state.education_xp += xp_gain

            # Consumption Value
            fallback_price = config.default_fallback_price
            price = new_state.perceived_avg_prices.get(item_id, fallback_price)
            consumption_value = quantity * price

            new_state.current_consumption += consumption_value

            # Food tracking
            if item_id in ["food", "basic_food", "luxury_food"]:
                new_state.current_food_consumption += consumption_value

            # Utility / Needs
            total_utility = 0.0
            utility_map = goods_info.get("utility_effects") or goods_info.get("utility_per_need")
            if utility_map:
                for need_type, utility_value in utility_map.items():
                    if need_type in new_needs:
                        satisfaction_gain = utility_value * quantity
                        total_utility += satisfaction_gain
                        new_needs[need_type] = max(0.0, new_needs.get(need_type, 0.0) - satisfaction_gain)

            return new_state, new_needs, ConsumptionResult(items_consumed={item_id: quantity}, satisfaction=total_utility)

        return new_state, new_needs, ConsumptionResult(items_consumed={}, satisfaction=0.0)

    def decide_and_consume(
        self,
        state: EconStateDTO,
        needs: Dict[str, float],
        current_time: int,
        goods_info_map: Dict[str, Any],
        config: HouseholdConfigDTO
    ) -> Tuple[EconStateDTO, Dict[str, float], Dict[str, float]]:
        """
        Decides what to consume from inventory based on needs and executes consumption.
        Logic migrated from EconComponent.decide_and_consume.
        """
        new_state = state # We will update state iteratively via consume, which returns new state

        final_needs = needs.copy()
        consumed_items: Dict[str, float] = {}

        # Iterate over inventory items
        inventory_items = list(state.inventory.items())

        for item_id, inventory_quantity in inventory_items:
            if inventory_quantity <= 0:
                continue

            good_info = goods_info_map.get(item_id)
            if not good_info:
                continue

            utility_effects = good_info.get("utility_effects", {})
            if not utility_effects:
                continue

            should_consume = False
            for need_key, effect in utility_effects.items():
                current_need = final_needs.get(need_key, 0.0)

                # Consumption Threshold
                threshold = config.need_medium_threshold
                if need_key == "survival":
                    threshold = config.survival_need_consumption_threshold

                if current_need > threshold:
                    should_consume = True
                    break

            if should_consume:
                is_durable = good_info.get("is_durable", False)
                if is_durable:
                    if inventory_quantity < 1.0:
                        continue
                    quantity_to_consume = 1.0
                else:
                    quantity_to_consume = min(inventory_quantity, 1.0)

                if quantity_to_consume > 0:
                    # Call self.consume
                    new_state, updated_needs, _ = self.consume(
                        new_state,
                        final_needs,
                        item_id,
                        quantity_to_consume,
                        current_time,
                        good_info,
                        config
                    )
                    final_needs = updated_needs
                    consumed_items[item_id] = consumed_items.get(item_id, 0.0) + quantity_to_consume

        return new_state, final_needs, consumed_items
