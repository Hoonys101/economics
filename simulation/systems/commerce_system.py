from __future__ import annotations
from typing import Dict, Any, List, Optional
import logging
from simulation.systems.api import ICommerceSystem, CommerceContext
from simulation.config import SimulationConfig
from simulation.systems.reflux_system import EconomicRefluxSystem

logger = logging.getLogger(__name__)

class CommerceSystem(ICommerceSystem):
    """틱의 소비 및 여가 부분을 관리하는 시스템."""

    def __init__(self, config: SimulationConfig, reflux_system: EconomicRefluxSystem):
        self.config = config
        self.reflux_system = reflux_system

    def execute_consumption_and_leisure(self, context: CommerceContext) -> None:
        """가계 소비, 긴급 구매(fast-track purchases), 여가 효과를 조율합니다."""
        households = context['households']
        breeding_planner = context['breeding_planner']
        household_time_allocation = context['household_time_allocation']
        market_data = context['market_data']
        time = context['time']

        # Inject analyzer if provided
        labor_market_analyzer = context.get('labor_market_analyzer')

        # WO-051: Vectorized Consumption Logic
        batch_decisions = breeding_planner.decide_consumption_batch(households, market_data)
        consume_list = batch_decisions.get('consume', [0] * len(households))
        buy_list = batch_decisions.get('buy', [0] * len(households))
        food_price = batch_decisions.get('price', 5.0)

        for i, household in enumerate(households):
            if not household.is_active:
                continue

            # 1. Consumption (Vectorized Optimization)
            consumed_items = {}

            # 1a. Fast Consumption
            if i < len(consume_list):
                c_amt = consume_list[i]
                if c_amt > 0:
                    household.consume("basic_food", c_amt, time)
                    consumed_items["basic_food"] = c_amt

            # 1b. Fast Purchase
            if i < len(buy_list):
                b_amt = buy_list[i]
                if b_amt > 0:
                    cost = b_amt * food_price
                    if household.assets >= cost:
                        household.assets -= cost
                        household.inventory["basic_food"] = household.inventory.get("basic_food", 0) + b_amt
                        self.reflux_system.capture(cost, source=f"Household_{household.id}", category="emergency_food")

                        if c_amt == 0:
                            food_consumption_quantity = getattr(self.config, "FOOD_CONSUMPTION_QUANTITY", 1.0)
                            consume_now = min(b_amt, food_consumption_quantity)
                            household.consume("basic_food", consume_now, time)
                            consumed_items["basic_food"] = consume_now

            # 2. Leisure Effect Application
            leisure_hours = household_time_allocation.get(household.id, 0.0)
            effect_dto = household.apply_leisure_effect(leisure_hours, consumed_items)

            # Store utility for reward injection
            household.last_leisure_utility = effect_dto.utility_gained

            # 3. Lifecycle Update
            # Construct LifecycleContext
            lifecycle_context = {
                'household': household,
                'market_data': market_data,
                'time': time
            }
            if labor_market_analyzer:
                lifecycle_context['labor_market_analyzer'] = labor_market_analyzer

            # Delegate to Household's update_needs (which calls AgentLifecycleComponent.run_tick)
            # But Household.update_needs doesn't accept the context directly, it accepts args.
            # We must rely on Household constructing the context correctly, but Household doesn't know about the analyzer.
            # So we call the component directly? Or we update Household interface?

            # Household.update_needs(time, market_data) constructs the context.
            # It misses 'labor_market_analyzer'.
            # I cannot change Household signature easily without breaking other tests maybe?
            # But I modified Household.update_needs to construct context.
            # If I modify Household to accept analyzer, I can pass it.
            # BUT `update_needs` is an override from BaseAgent? BaseAgent.update_needs signature?
            # BaseAgent: def update_needs(self, current_time: int, government: Optional[Any] = None, market_data: Optional[Dict[str, Any]] = None, reflux_system: Optional[Any] = None, technology_manager: Optional[Any] = None) -> None:
            # It's flexible.

            # Ideally, `AgentLifecycleComponent` should be called directly if we want to pass specific context.
            # `household.lifecycle_component.run_tick(lifecycle_context)`
            # This bypasses `household.update_needs`.
            # Is that okay? `CommerceSystem` is the new orchestrator.
            # `household.update_needs` was the old orchestrator.
            # Yes, calling component directly is cleaner here.

            household.lifecycle_component.run_tick(lifecycle_context)

            # Apply XP to Children
            if effect_dto.leisure_type == "PARENTING" and effect_dto.xp_gained > 0:
                for child_id in household.children_ids:
                    child = next((h for h in households if h.id == child_id), None)
                    if child and child.is_active:
                        child.education_xp += effect_dto.xp_gained
