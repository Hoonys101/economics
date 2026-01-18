from __future__ import annotations
from typing import Dict, List, Any
import logging

from simulation.systems.api import ICommerceSystem, CommerceContext

logger = logging.getLogger(__name__)

class CommerceSystem(ICommerceSystem):
    """
    Manages consumption, fast-track purchases, and leisure effects.
    Extracts consumption and leisure logic from Simulation.run_tick.
    """

    def __init__(self, config, reflux_system):
        self.config = config
        self.reflux_system = reflux_system

    def execute_consumption_and_leisure(self, context: CommerceContext) -> None:
        """
        Coordinates consumption, purchases, and leisure for all households.
        """
        households = context["households"]
        breeding_planner = context["breeding_planner"]
        household_time_allocation = context["household_time_allocation"]
        # reflux_system is injected in __init__ but also available in context if needed,
        # but spec says __init__(config, reflux_system).
        # API says execute_consumption_and_leisure(context).
        # Context has reflux_system too. We can use either.
        # I'll use the one in context to follow the pattern or self.reflux_system.
        # The api definition in my thought block had reflux_system in CommerceContext.

        market_data = context["market_data"]
        time = context["time"]

        # Create a consumption-specific market data context
        # In Simulation.run_tick, this was done before calling this logic.
        # Here we assume market_data is already prepared or we modify it.
        # Simulation logic added "job_vacancies" to consumption_market_data.
        # We should probably do that here or assume it's passed.
        # The spec says "CommerceContext has market_data".

        # WO-051: Vectorized Consumption Logic
        # Pre-calculate consumption/purchase decisions for all households
        batch_decisions = breeding_planner.decide_consumption_batch(households, market_data)
        consume_list = batch_decisions.get('consume', [0] * len(households))
        buy_list = batch_decisions.get('buy', [0] * len(households))
        food_price = batch_decisions.get('price', 5.0)  # Default food price

        for i, household in enumerate(households):
             if household.is_active:

                 # 1. Consumption (Vectorized Optimization)
                 consumed_items = {}

                 # 1a. Fast Consumption (Basic Food)
                 if i < len(consume_list):
                     c_amt = consume_list[i]
                     if c_amt > 0:
                         # Use household.consume which delegates to economy_manager
                         household.consume("basic_food", c_amt, time)
                         consumed_items["basic_food"] = c_amt

                 # 1b. Fast Purchase (Survival Rescue - Logic Map Item 3)
                 if i < len(buy_list):
                     b_amt = buy_list[i]
                     if b_amt > 0:
                         cost = b_amt * food_price
                         if household.assets >= cost:
                             household.assets -= cost
                             household.inventory["basic_food"] = household.inventory.get("basic_food", 0) + b_amt
                             # To prevent money destruction, we route this to Reflux System (Sink)
                             self.reflux_system.capture(cost, source=f"Household_{household.id}", category="emergency_food")
                             logger.debug(
                                 f"VECTOR_BUY | Household {household.id} bought {b_amt:.1f} food (Fast Track)",
                                 extra={"agent_id": household.id, "tags": ["consumption", "vector_buy"]}
                             )

                             if c_amt == 0:
                                 consume_now = min(b_amt, getattr(self.config, "FOOD_CONSUMPTION_QUANTITY", 1.0))
                                 household.consume("basic_food", consume_now, time)
                                 consumed_items["basic_food"] = consume_now

                 # 2. Phase 5: Leisure Effect Application
                 leisure_hours = household_time_allocation.get(household.id, 0.0)
                 effect_dto = household.apply_leisure_effect(leisure_hours, consumed_items)

                 # 3. Lifecycle Update [BUGFIX: WO-Diag-003]
                 # Note: Household.update_needs will be refactored to use AgentLifecycleComponent
                 # But the method name on Household remains update_needs for compatibility or
                 # the system calls AgentLifecycleComponent directly?
                 # The spec says "CommerceSystem ... calls household.update_needs ... which will be refactored to AgentLifecycleComponent.run_tick".
                 # So we call household.update_needs(time, market_data) here.
                 household.update_needs(time, market_data)

                 # Store utility for reward injection (Simulation used to do this)
                 # Wait, CommerceSystem doesn't return this map.
                 # Simulation logic used `household_leisure_effects` map later for AI learning.
                 # The Spec for CommerceSystem doesn't mention returning this map.
                 # But `execute_consumption_and_leisure` returns None.
                 # How does Simulation get `leisure_utility` for AI reward?
                 # It seems I might need to store it in household or return it.
                 # The household.apply_leisure_effect returns effect_dto.
                 # Maybe we can store it on the household object transiently?
                 # Or update the API to return the map.
                 # For now, I'll store it in household.leisure_utility_this_tick to be safe/clean.
                 household.leisure_utility_this_tick = effect_dto.utility_gained

                 # Apply XP to Children (if Parenting)
                 if effect_dto.leisure_type == "PARENTING" and effect_dto.xp_gained > 0:
                     for child_id in household.children_ids:
                         # Children might be in self.agents
                         # We need access to all agents to find child.
                         # Context has 'households' list.
                         # We can look up in 'households' list if child is a household.
                         # Simulation had access to self.agents.
                         # CommerceContext only has households list.
                         # Assuming children are in the households list.
                         child = next((h for h in households if h.id == child_id), None)

                         if child and child.is_active:
                             child.education_xp += effect_dto.xp_gained
                             logger.debug(
                                 f"PARENTING_XP_TRANSFER | Parent {household.id} -> Child {child_id}. XP: {effect_dto.xp_gained:.4f}",
                                 extra={"agent_id": household.id, "tags": ["LEISURE_EFFECT", "parenting"]}
                             )
