from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
import logging

from modules.household.api import IDecisionUnit, OrchestrationContextDTO
from modules.household.dtos import EconStateDTO
from simulation.dtos import StressScenarioConfig
from simulation.models import Order

# New Imports
from modules.market.housing_planner import HousingPlanner
from modules.housing.dtos import (
    HousingDecisionRequestDTO,
    HousingPurchaseDecisionDTO,
    HousingRentalDecisionDTO,
    HousingStayDecisionDTO
)

if TYPE_CHECKING:
    from simulation.dtos.config_dtos import HouseholdConfigDTO

logger = logging.getLogger(__name__)

class DecisionUnit(IDecisionUnit):
    """
    Stateless unit responsible for coordinating decision making.
    Wraps DecisionEngine and System 2 logic (Orchestration).
    """

    def __init__(self):
        self.housing_planner = HousingPlanner()

    def orchestrate_economic_decisions(
        self,
        state: EconStateDTO,
        context: OrchestrationContextDTO,
        initial_orders: List[Order]
    ) -> Tuple[EconStateDTO, List[Order]]:
        """
        Refines orders and updates internal economic state.
        Includes System 2 Housing Logic and Shadow Wage Logic.
        Logic migrated from EconComponent.orchestrate_economic_decisions.
        """
        new_state = state.copy()
        refined_orders = list(initial_orders) # Copy list

        # Unpack from DTO
        market_snapshot = context["market_snapshot"]
        current_time = context["current_time"]
        config = context["config"]
        stress_scenario_config = context["stress_scenario_config"]
        household_state = context["household_state"]
        housing_system = context.get("housing_system")

        # 1. System 2 Housing Decision Logic (Delegated to HousingPlanner)
        if new_state.is_homeless or current_time % 30 == 0:
             # Construct Request
             request = HousingDecisionRequestDTO(
                 household_state=household_state,
                 housing_market_snapshot=market_snapshot.housing,
                 outstanding_debt_payments=0.0 # Placeholder: Planner uses assets check primarily
             )

             # Call Planner
             decision = self.housing_planner.evaluate_housing_options(request)

             # Process Decision
             if decision['decision_type'] == "INITIATE_PURCHASE":
                 if housing_system and hasattr(housing_system, 'initiate_purchase'):
                     # Dispatch to Saga Handler
                     housing_system.initiate_purchase(decision, buyer_id=state.portfolio.owner_id)
                     new_state.housing_target_mode = "BUY"
                 else:
                     # logger.warning("Housing System not available for purchase initiation.")
                     pass

             elif decision['decision_type'] == "MAKE_RENTAL_OFFER":
                 # Future: Create Rent Order. For now, we update target mode.
                 new_state.housing_target_mode = "RENT"
                 # If we had a mechanism to rent, we would append order here.

             elif decision['decision_type'] == "STAY":
                 new_state.housing_target_mode = "STAY"


        # 2. Shadow Labor Market Logic
        avg_market_wage = market_snapshot.labor.avg_wage

        if avg_market_wage > 0:
            new_state.market_wage_history.append(avg_market_wage)

        if new_state.shadow_reservation_wage <= 0.0:
            new_state.shadow_reservation_wage = new_state.current_wage if new_state.is_employed else new_state.expected_wage

        if new_state.is_employed:
            target = max(new_state.current_wage, new_state.shadow_reservation_wage)
            new_state.shadow_reservation_wage = (new_state.shadow_reservation_wage * 0.95) + (target * 0.05)
        else:
            new_state.shadow_reservation_wage *= (1.0 - 0.02)
            min_wage = config.household_min_wage_demand
            if new_state.shadow_reservation_wage < min_wage:
                new_state.shadow_reservation_wage = min_wage

        # 4. Panic Selling
        if stress_scenario_config and stress_scenario_config.is_active and stress_scenario_config.scenario_name == 'deflation':
             threshold = config.panic_selling_asset_threshold
             if new_state.assets < threshold:
                 # Sell stocks
                 for firm_id, share in new_state.portfolio.holdings.items():
                     if share.quantity > 0:
                         stock_order = Order(
                             agent_id=state.portfolio.owner_id,
                             side="SELL",
                             item_id=f"stock_{firm_id}",
                             quantity=share.quantity,
                             price_limit=0.0,
                             market_id="stock_market"
                         )
                         refined_orders.append(stock_order)

        # 5. Targeted Order Refinement (Logic from original)
        if stress_scenario_config and stress_scenario_config.is_active and stress_scenario_config.scenario_name == 'phase29_depression':
             multiplier = stress_scenario_config.demand_shock_multiplier
             if multiplier is not None:
                 for order in refined_orders:
                     if order.side == "BUY" and hasattr(order, "item_id") and order.item_id not in ["labor", "loan"]:
                         if not order.item_id.startswith("stock_"):
                            order.quantity *= multiplier

        # 6. Forensics (Shadow Wage Update)
        for order in refined_orders:
             if order.side == "SELL" and (getattr(order, "item_id", "") == "labor" or order.market_id == "labor"):
                new_state.last_labor_offer_tick = current_time

        return new_state, refined_orders
