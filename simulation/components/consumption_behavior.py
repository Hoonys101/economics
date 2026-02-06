from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Dict, Any, Optional

if TYPE_CHECKING:
    from simulation.core_agents import Household

logger = logging.getLogger(__name__)

class ConsumptionBehavior:
    """
    Phase 22.5: Household Consumption Component
    Handles inventory-based consumption decisions and utility application.
    """

    def __init__(self, owner: "Household", config_module: Any):
        self.owner = owner
        self.config = config_module

    def decide_and_consume(self, current_time: int, market_data: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """
        Consumes goods from inventory based on need thresholds.
        """
        consumed_items: Dict[str, float] = {}
        log_extra = {"tick": current_time, "agent_id": self.owner.id, "tags": ["consumption"]}

        # 1. Evaluate items in inventory
        for item_id, inventory_quantity in list(self.owner._econ_state.inventory.items()):
            if inventory_quantity <= 0:
                continue

            good_info = self.owner.goods_info_map.get(item_id)
            if not good_info:
                continue

            utility_effects = good_info.get("utility_effects", {})
            if not utility_effects:
                continue

            should_consume = False
            for need_key, effect in utility_effects.items():
                current_need = self.owner.needs.get(need_key, 0.0)
                
                # Consumption Threshold
                threshold = self.config.NEED_MEDIUM_THRESHOLD
                if need_key == "survival":
                    threshold = self.config.SURVIVAL_NEED_CONSUMPTION_THRESHOLD
                
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
                    self.owner.consume(item_id, quantity_to_consume, current_time)
                    consumed_items[item_id] = consumed_items.get(item_id, 0.0) + quantity_to_consume
                    
                    logger.debug(
                        f"CONSUMPTION | {self.owner.id} consumed {quantity_to_consume:.2f} {item_id}.",
                        extra={**log_extra, "item_id": item_id, "quantity": quantity_to_consume}
                    )

        # 2. Update Needs (Natural Decay/Growth handled by PsychologyComponent usually)
        # Note: In engine.py, decide_and_consume used to call update_needs.
        # We will keep that structure or call it from Household.
        return consumed_items
