"""
Implements the CommerceSystem which orchestrates consumption, purchases, and leisure.
"""
from typing import Any, Dict, List, Optional, Tuple
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

    def plan_consumption_and_leisure(self, context: CommerceContext, scenario_config: Optional["StressScenarioConfig"] = None) -> Tuple[Dict[int, Dict[str, Any]], List[Any]]:
        """
        Phase 1 (Decisions): Determines desired consumption and leisure type.
        Returns:
            Tuple[Dict, List[Order]]: (Consumption Plans, Generated Orders)
        """
        from simulation.models import Order

        households = context["households"]
        breeding_planner = context["breeding_planner"]
        time_allocation = context["household_time_allocation"]
        market_data = context["market_data"]
        current_time = context["time"]

        planned_consumption = {}
        generated_orders = []

        # 1. Vectorized Decision Making
        batch_decisions = breeding_planner.decide_consumption_batch(households, market_data)

        consume_list = batch_decisions.get('consume', [0] * len(households))
        buy_list = batch_decisions.get('buy', [0] * len(households))
        food_price = batch_decisions.get('price', 5.0)

        for i, household in enumerate(households):
            if not household.is_active:
                continue

            plan = {
                "consume_amt": 0.0,
                "buy_amt": 0.0,
                "leisure_hours": time_allocation.get(household.id, 0.0)
            }

            # 2a. Plan Consumption
            if i < len(consume_list):
                c_amt = consume_list[i]

                # Phase 28: Deflationary Spiral
                if scenario_config and scenario_config.is_active and scenario_config.scenario_name == 'deflation':
                    if not household.is_employed and scenario_config.consumption_pessimism_factor > 0:
                        c_amt *= (1 - scenario_config.consumption_pessimism_factor)

                if c_amt > 0:
                    plan["consume_amt"] = c_amt

            # 2b. Plan Purchase (Generate Order)
            if i < len(buy_list):
                b_amt = buy_list[i]
                if b_amt > 0:
                    # Create Order instead of direct execution
                    order = Order(
                        agent_id=household.id,
                        order_type="BUY",
                        item_id="basic_food",
                        quantity=b_amt,
                        price=food_price * 1.5, # Willing to pay premium
                        market_id="basic_food"
                    )
                    generated_orders.append(order)
                    plan["buy_amt"] = b_amt

            planned_consumption[household.id] = plan

        return planned_consumption, generated_orders

    def finalize_consumption_and_leisure(self, context: CommerceContext, planned_consumption: Dict[int, Dict[str, Any]]) -> Dict[int, float]:
        """
        Phase 4 (Lifecycle): Executes consumption from inventory and applies leisure effects.
        """
        households = context["households"]
        current_time = context["time"]

        household_leisure_effects: Dict[int, float] = {}

        for household in households:
            if not household.is_active:
                continue

            plan = planned_consumption.get(household.id, {})
            consume_amt = plan.get("consume_amt", 0.0)
            leisure_hours = plan.get("leisure_hours", 0.0)

            consumed_items = {}

            # Execute Consumption (Eat from Inventory)
            if consume_amt > 0:
                household.consume("basic_food", consume_amt, current_time)
                consumed_items["basic_food"] = consume_amt

            # Apply Leisure Effect
            effect_dto = household.apply_leisure_effect(leisure_hours, consumed_items)
            household_leisure_effects[household.id] = effect_dto.utility_gained

            # Parenting XP Transfer
            if effect_dto.leisure_type == "PARENTING" and effect_dto.xp_gained > 0:
                agents = context.get("agents", {})
                for child_id in household.children_ids:
                    child = agents.get(child_id)
                    if child and getattr(child, "is_active", False):
                        child.education_xp += effect_dto.xp_gained

            # CRITICAL: household.update_needs() is NOT called here.
            # It is assumed to be called by AgentLifecycleManager in Phase 4.

        return household_leisure_effects
