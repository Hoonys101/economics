from __future__ import annotations
from typing import TYPE_CHECKING, Dict

from simulation.dtos import ConsumptionResult

if TYPE_CHECKING:
    from simulation.core_agents import Household


class EconomyManager:
    """
    Manages all economic activities for a Household.

    This component handles consumption, saving, tax payments, and inventory
    valuation, separating these concerns from the core Household agent logic.
    """

    def __init__(self, household: "Household", config_module: any) -> None:
        """
        Initializes the EconomyManager.

        Args:
            household: The household agent that owns this manager.
            config_module: The simulation's configuration module.
        """
        self._household = household
        self._config = config_module

    def consume(
        self, item_id: str, quantity: float, current_time: int
    ) -> ConsumptionResult:
        """
        Consumes a specified quantity of an item from the household's inventory.

        This method contains the logic moved from `Household.consume`.

        Args:
            item_id: The ID of the item to consume.
            quantity: The amount of the item to consume.
            current_time: The current simulation tick.

        Returns:
            A ConsumptionResult DTO containing the consumed items and satisfaction.
        """
        log_extra = {
            "tick": current_time,
            "agent_id": self._household.id,
            "item_id": item_id,
            "quantity": quantity,
            "tags": ["household_consumption"],
        }
        total_utility = 0.0
        self._household.logger.debug(
            f"CONSUME_START | Household {self._household.id} attempting to consume: Item={item_id}, Qty={quantity:.1f}, Inventory={self._household.get_quantity(item_id):.1f}",
            extra=log_extra,
        )
        good_info = self._household.goods_info_map.get(item_id, {})
        is_service = good_info.get("is_service", False)

        if is_service or self._household.get_quantity(item_id) >= quantity:
            if not is_service:
                self._household.remove_item(item_id, quantity)

            # Durable goods logic
            is_durable = good_info.get("is_durable", False)
            if is_durable and not is_service:
                base_lifespan = good_info.get("base_lifespan", 50)
                quality = self._household.get_quality(item_id)
                num_assets = int(round(quantity))
                for _ in range(num_assets):
                    asset = {
                        "item_id": item_id,
                        "quality": quality,
                        "remaining_life": base_lifespan,
                    }
                    self._household.add_durable_asset(asset)

            # Education XP logic
            if item_id == "education_service":
                xp_gain = quantity * self._config.LEARNING_EFFICIENCY
                self._household.add_education_xp(xp_gain)

            # FIX: Calculate consumption value based on price
            fallback_price = getattr(self._config, "DEFAULT_FALLBACK_PRICE", 5.0)
            price = self._household.perceived_avg_prices.get(item_id, fallback_price)
            consumption_value = quantity * price

            self._household.current_consumption += consumption_value

            # FIX: Track food consumption for Engel Coefficient
            if item_id in ["food", "basic_food", "luxury_food"]:
                self._household.current_food_consumption += consumption_value

            utility_map = good_info.get("utility_effects") or good_info.get(
                "utility_per_need"
            )
            if utility_map:
                for need_type, utility_value in utility_map.items():
                    if need_type in self._household.needs:
                        satisfaction_gain = utility_value * quantity
                        total_utility += satisfaction_gain
                        self._household.needs[need_type] = max(
                            0,
                            self._household.needs.get(need_type, 0)
                            - satisfaction_gain,
                        )
            return ConsumptionResult(
                items_consumed={item_id: quantity}, satisfaction=total_utility
            )

        return ConsumptionResult(items_consumed={}, satisfaction=0)

    def pay_taxes(self) -> None:
        """
        Handles the logic for paying taxes.
        """
        # In the current simulation, taxes are deducted by the Government agent,
        # so this is a placeholder for now.
        pass

    def save(self) -> None:
        """
        Handles the logic for saving.
        """
        # Saving is currently implicit (income not spent), so this is a placeholder.
        pass

    def get_inventory_value(self) -> float:
        """
        Calculates the total value of the household's inventory based on perceived prices.

        Returns:
            The total monetary value of the household's inventory.
        """
        total_value = 0.0
        for item_id, quantity in self._household._econ_state.inventory.items():
            price = self._household.perceived_avg_prices.get(item_id, 0)
            total_value += quantity * price
        return total_value
