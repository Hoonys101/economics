from __future__ import annotations
from typing import List, Dict, Any, Optional
import logging

from modules.household.api import IBudgetEngine, BudgetInputDTO, BudgetOutputDTO, BudgetPlan, HousingActionDTO, PrioritizedNeed
from modules.household.dtos import EconStateDTO, HouseholdSnapshotDTO
from modules.market.housing_planner import HousingPlanner
from modules.housing.dtos import HousingDecisionRequestDTO
from modules.system.api import DEFAULT_CURRENCY

logger = logging.getLogger(__name__)

SHADOW_WAGE_DECAY = 0.95
SHADOW_WAGE_TARGET_WEIGHT = 0.05
SHADOW_WAGE_UNEMPLOYED_DECAY = 0.02
HOUSING_CHECK_FREQUENCY = 30
DEFAULT_FOOD_PRICE_ESTIMATE = 10.0
DEFAULT_SURVIVAL_BUDGET = 50.0

class BudgetEngine(IBudgetEngine):
    """
    Stateless engine managing financial planning, budgeting, and housing decisions.
    Logic migrated from DecisionUnit and EconComponent.
    """

    def __init__(self):
        self.housing_planner = HousingPlanner()

    def allocate_budget(self, input_dto: BudgetInputDTO) -> BudgetOutputDTO:
        econ_state = input_dto.econ_state
        prioritized_needs = input_dto.prioritized_needs
        abstract_plan = input_dto.abstract_plan
        market_snapshot = input_dto.market_snapshot
        config = input_dto.config
        current_tick = input_dto.current_tick

        new_econ_state = econ_state.copy()

        # 1. Shadow Wage Update (Planning)
        self._update_shadow_wage(new_econ_state, market_snapshot, config, current_tick)

        # 2. Housing Decision (Strategic Planning)
        housing_action = self._plan_housing(new_econ_state, market_snapshot, current_tick)

        # 3. Budget Allocation
        budget_plan = self._create_budget_plan(
            new_econ_state, prioritized_needs, abstract_plan, market_snapshot, config
        )

        return BudgetOutputDTO(
            econ_state=new_econ_state,
            budget_plan=budget_plan,
            housing_action=housing_action
        )

    def _update_shadow_wage(self, state: EconStateDTO, market_snapshot: Any, config: Any, current_tick: int):
        # Logic from DecisionUnit.orchestrate_economic_decisions (Shadow Wage part)
        avg_market_wage = market_snapshot.labor.avg_wage if hasattr(market_snapshot, "labor") else 0.0

        if avg_market_wage > 0:
            state.market_wage_history.append(avg_market_wage)

        if state.shadow_reservation_wage <= 0.0:
            state.shadow_reservation_wage = state.current_wage if state.is_employed else state.expected_wage

        if state.is_employed:
            target = max(state.current_wage, state.shadow_reservation_wage)
            state.shadow_reservation_wage = (state.shadow_reservation_wage * SHADOW_WAGE_DECAY) + (target * SHADOW_WAGE_TARGET_WEIGHT)
        else:
            state.shadow_reservation_wage *= (1.0 - SHADOW_WAGE_UNEMPLOYED_DECAY)
            min_wage = config.household_min_wage_demand
            if state.shadow_reservation_wage < min_wage:
                state.shadow_reservation_wage = min_wage

    def _plan_housing(self, state: EconStateDTO, market_snapshot: Any, current_tick: int) -> Optional[HousingActionDTO]:
        # Logic from DecisionUnit housing part
        if state.is_homeless or current_tick % HOUSING_CHECK_FREQUENCY == 0:
            # We need to construct a wrapper that mimics HouseholdSnapshotDTO or just has econ_state
            # HousingPlanner expects `request['household_state']` which has `.econ_state`.

            # Simple wrapper class
            class StateWrapper:
                def __init__(self, e_state):
                    self.econ_state = e_state

            wrapper = StateWrapper(state)

            # Ensure market_snapshot has housing
            housing_snap = market_snapshot.housing if hasattr(market_snapshot, "housing") else None

            if housing_snap:
                request = HousingDecisionRequestDTO(
                    household_state=wrapper,
                    housing_market_snapshot=housing_snap,
                    outstanding_debt_payments=0.0
                )

                decision = self.housing_planner.evaluate_housing_options(request)

                # Convert decision to HousingActionDTO and update state intention
                if decision['decision_type'] == "INITIATE_PURCHASE":
                    state.housing_target_mode = "BUY"
                    return HousingActionDTO(
                        action_type="INITIATE_PURCHASE",
                        property_id=str(decision['target_property_id']),
                        offer_price=decision['offer_price'],
                        down_payment_amount=decision.get('down_payment_amount', 0.0)
                    )
                elif decision['decision_type'] == "MAKE_RENTAL_OFFER":
                    state.housing_target_mode = "RENT"
                    return HousingActionDTO(
                        action_type="MAKE_RENTAL_OFFER",
                        property_id=str(decision['target_property_id'])
                    )
                elif decision['decision_type'] == "STAY":
                    state.housing_target_mode = "STAY"
                    return HousingActionDTO(action_type="STAY")

        return None

    def _create_budget_plan(
        self,
        state: EconStateDTO,
        needs: List[PrioritizedNeed],
        abstract_plan: List[Any],
        market_snapshot: Any,
        config: Any = None # Optional for backward compatibility in internal calls, but should be passed
    ) -> BudgetPlan:
        # Simple Budgeting:
        # 1. Total Wealth = Cash
        total_cash = state.wallet.get_balance(DEFAULT_CURRENCY)

        allocations = {}
        spent = 0.0

        # 2. Allocate for Needs (Survival first)
        for need in needs:
            # Estimate cost.
            # E.g. Survival -> Food.
            if need.need_id == "survival":
                # Estimate food cost.
                food_price = config.default_food_price_estimate if config else DEFAULT_FOOD_PRICE_ESTIMATE
                goods_market = getattr(market_snapshot, "goods", {})

                # Check different keys for food
                m = goods_market.get("basic_food") or goods_market.get("food")
                if m:
                    # MarketSnapshotDTO uses GoodsMarketUnitDTO which has avg_price
                    food_price = getattr(m, "avg_price", food_price) or getattr(m, "current_price", food_price)

                # Quantity: Place enough for buffer?
                # Placeholder: Allocate fixed amount
                amount_to_allocate = config.survival_budget_allocation if config else DEFAULT_SURVIVAL_BUDGET
                if total_cash - spent >= amount_to_allocate:
                    allocations["food"] = amount_to_allocate
                    spent += amount_to_allocate
                else:
                    allocations["food"] = max(0.0, total_cash - spent)
                    spent = total_cash

            # Other needs...

        # 3. Allocate for Abstract Plan (AI Orders)
        # If AI says "Buy Stock", allocate.
        approved_orders = []
        for order in abstract_plan:
            if order.side == "BUY":
                cost = order.quantity * order.price_limit
                if total_cash - spent >= cost:
                    item_type = "investment" if "stock" in order.item_id else "goods"
                    allocations[item_type] = allocations.get(item_type, 0.0) + cost
                    spent += cost
                    approved_orders.append(order)
            elif order.side == "SELL":
                approved_orders.append(order)

        return BudgetPlan(
            allocations=allocations,
            discretionary_spending=max(0.0, total_cash - spent),
            orders=approved_orders
        )
