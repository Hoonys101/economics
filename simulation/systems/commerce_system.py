"""
Implements the CommerceSystem which orchestrates consumption, purchases, and leisure.
"""
from typing import Any, Dict, List
import logging
from simulation.systems.api import ICommerceSystem, CommerceContext
from simulation.systems.reflux_system import EconomicRefluxSystem

logger = logging.getLogger(__name__)

class CommerceSystem(ICommerceSystem):
    """
    Orchestrates the consumption and leisure phase of the tick.
    """

    def __init__(self, config: Any, reflux_system: EconomicRefluxSystem):
        self.config = config
        self.reflux_system = reflux_system

    def execute_consumption_and_leisure(self, context: CommerceContext) -> Dict[int, float]:
        """
        Executes vectorized consumption, applies fast-track purchases,
        and calculates leisure effects.

        Returns:
            Dict[int, float]: Map of Household ID to Utility Gained.
        """
        households = context["households"]
        breeding_planner = context["breeding_planner"]
        time_allocation = context["household_time_allocation"]
        market_data = context["market_data"]
        current_time = context["time"]

        household_leisure_effects: Dict[int, float] = {}

        # 1. Vectorized Decision Making
        batch_decisions = breeding_planner.decide_consumption_batch(households, market_data)

        consume_list = batch_decisions.get('consume', [0] * len(households))
        buy_list = batch_decisions.get('buy', [0] * len(households))
        food_price = batch_decisions.get('price', 5.0)

        for i, household in enumerate(households):
            if not household.is_active:
                continue

            consumed_items = {}

            # 2a. Fast Consumption
            if i < len(consume_list):
                c_amt = consume_list[i]
                if c_amt > 0:
                    household.consume("basic_food", c_amt, current_time)
                    consumed_items["basic_food"] = c_amt

            # 2b. Fast Purchase (Emergency Buy)
            if i < len(buy_list):
                b_amt = buy_list[i]
                if b_amt > 0:
                    cost = b_amt * food_price
                    if household.assets >= cost:
                        household.assets -= cost
                        household.inventory["basic_food"] = household.inventory.get("basic_food", 0) + b_amt

                        # Capture money sink
                        self.reflux_system.capture(cost, source=f"Household_{household.id}", category="emergency_food")

                        logger.debug(
                            f"VECTOR_BUY | Household {household.id} bought {b_amt:.1f} food (Fast Track)",
                            extra={"agent_id": household.id, "tags": ["consumption", "vector_buy"]}
                        )

                        # Immediate consumption if needed
                        if c_amt == 0:
                            consume_now = min(b_amt, getattr(self.config, "FOOD_CONSUMPTION_QUANTITY", 1.0))
                            household.consume("basic_food", consume_now, current_time)
                            consumed_items["basic_food"] = consume_now

            # 3. Leisure Effect
            leisure_hours = time_allocation.get(household.id, 0.0)
            effect_dto = household.apply_leisure_effect(leisure_hours, consumed_items)

            household_leisure_effects[household.id] = effect_dto.utility_gained

            # 4. Lifecycle Update (Needs, Tax, Psychology)
            # This is now delegated to AgentLifecycleComponent inside household.update_needs
            # But wait, household.update_needs calls labor_manager.work()!
            # work() shouldn't be called here if it was already done or calculated.
            # In the old `Simulation.run_tick`:
            # - Transactions happened.
            # - Then this loop happened.
            # - household.update_needs() was called here.
            # - household.update_needs() calls labor_manager.work(8.0)

            # So we must call household.update_needs() here to maintain logic.
            # BUT, we are refactoring update_needs to AgentLifecycleComponent.
            # So we should call household.lifecycle.run_tick() ideally.
            # Since household still has update_needs wrapping the new component (in the intermediate step),
            # we call household.update_needs().

            household.update_needs(current_time, market_data)

            # 5. Parenting XP Transfer
            if effect_dto.leisure_type == "PARENTING" and effect_dto.xp_gained > 0:
                for child_id in household.children_ids:
                    # Find child in households list? Or need global agent lookup?
                    # The context only provides households list.
                    # We might need to iterate households list to find child.
                    child = next((h for h in households if h.id == child_id), None)
                    if child and child.is_active:
                        child.education_xp += effect_dto.xp_gained

        return household_leisure_effects
