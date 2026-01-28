"""
Implements the CommerceSystem which orchestrates consumption, purchases, and leisure.
"""
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
import logging
from simulation.systems.api import ICommerceSystem, CommerceContext
from simulation.models import Transaction

if TYPE_CHECKING:
    from simulation.dtos.scenario import StressScenarioConfig

logger = logging.getLogger(__name__)

class CommerceSystem(ICommerceSystem):
    """
    Orchestrates the consumption and leisure phase of the tick.
    """

    def __init__(self, config: Any):
        self.config = config

    def plan_consumption_and_leisure(self, context: CommerceContext, scenario_config: Optional["StressScenarioConfig"] = None) -> Tuple[Dict[int, Dict[str, Any]], List[Transaction]]:
        """
        Phase 1: Decisions.
        Determines desired consumption and generates transactions for Fast Purchase.
        Returns (PlannedConsumptionMap, Transactions).
        """
        households = context["households"]
        breeding_planner = context["breeding_planner"]
        market_data = context["market_data"]
        current_time = context["time"]

        planned_consumptions = {}
        transactions = []

        # 1. Vectorized Decision Making
        batch_decisions = breeding_planner.decide_consumption_batch(households, market_data)

        consume_list = batch_decisions.get('consume', [0] * len(households))
        buy_list = batch_decisions.get('buy', [0] * len(households))
        food_price = batch_decisions.get('price', 5.0)

        for i, household in enumerate(households):
            if not household.is_active:
                continue

            c_amt = 0.0
            if i < len(consume_list):
                c_amt = consume_list[i]
                # Phase 28: Deflationary Spiral - Consumption Collapse
                if scenario_config and scenario_config.is_active and scenario_config.scenario_name == 'deflation':
                    if not household.is_employed and scenario_config.consumption_pessimism_factor > 0:
                        original_amt = c_amt
                        c_amt *= (1 - scenario_config.consumption_pessimism_factor)
                        logger.debug(f"PESSIMISM_IMPACT | Household {household.id} consumption reduced from {original_amt:.2f} to {c_amt:.2f}")

            # Store plan
            planned_consumptions[household.id] = {
                "consume_amount": c_amt,
                "buy_amount": 0.0,
                "consumed_immediately_from_buy": 0.0
            }

            # 2b. Fast Purchase (Emergency Buy) -> Generate Transaction
            if i < len(buy_list):
                b_amt = buy_list[i]
                if b_amt > 0:
                    cost = b_amt * food_price
                    # Optimistic check (actual balance check in TransactionProcessor)
                    if household.assets >= cost:
                        planned_consumptions[household.id]["buy_amount"] = b_amt

                        # Use Government as Seller for Emergency Buy (Import/Reserve)
                        government = context.get("government")
                        seller_id = government.id if government else 999999

                        # Generate Emergency Buy Transaction
                        tx = Transaction(
                            buyer_id=household.id,
                            seller_id=seller_id,
                            item_id="basic_food",
                            quantity=b_amt,
                            price=food_price, # Unit Price
                            market_id="system",
                            transaction_type="emergency_buy",
                            time=current_time
                        )
                        transactions.append(tx)

                        logger.debug(
                            f"VECTOR_BUY_PLAN | Household {household.id} planning to buy {b_amt:.1f} food (Fast Track)",
                            extra={"agent_id": household.id, "tags": ["consumption", "vector_buy"]}
                        )

        return planned_consumptions, transactions

    def finalize_consumption_and_leisure(self, context: CommerceContext, planned_consumptions: Dict[int, Dict[str, Any]]) -> Dict[int, float]:
        """
        Phase 4: Lifecycle Effects.
        Executes consumption from inventory and applies leisure effects.
        """
        households = context["households"]
        time_allocation = context["household_time_allocation"]
        current_time = context["time"]

        household_leisure_effects: Dict[int, float] = {}

        for household in households:
            if not household.is_active:
                continue

            plan = planned_consumptions.get(household.id, {})
            c_amt = plan.get("consume_amount", 0.0)

            consumed_items = {}
            if c_amt > 0:
                household.consume("basic_food", c_amt, current_time)
                consumed_items["basic_food"] = c_amt

            # 3. Leisure Effect
            leisure_hours = time_allocation.get(household.id, 0.0)
            effect_dto = household.apply_leisure_effect(leisure_hours, consumed_items)

            household_leisure_effects[household.id] = effect_dto.utility_gained

            # 5. Parenting XP Transfer
            if effect_dto.leisure_type == "PARENTING" and effect_dto.xp_gained > 0:
                agents = context.get("agents", {})
                for child_id in household.children_ids:
                    # Use O(1) lookup from agents dict
                    child = agents.get(child_id)
                    if child and getattr(child, "is_active", False):
                        child.education_xp += effect_dto.xp_gained

        return household_leisure_effects
