from __future__ import annotations
from typing import List, Dict, Any, Optional
import logging
from decimal import Decimal

from modules.household.api import IBudgetEngine, BudgetInputDTO, BudgetOutputDTO, BudgetPlan, HousingActionDTO, PrioritizedNeed
from modules.household.dtos import EconStateDTO, HouseholdSnapshotDTO
from modules.market.housing_planner import HousingPlanner
from modules.housing.dtos import HousingDecisionRequestDTO
from modules.system.api import DEFAULT_CURRENCY
from simulation.models import Order
from modules.finance.utils.currency_math import round_to_pennies

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
    MIGRATION: Uses integer pennies for budget allocation.
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
        # Wage is now pennies in state, but logic often uses floats.
        # Let's keep shadow wage logic in pennies.

        # Market avg wage is usually dollars (float)?
        # MarketSnapshotDTO.labor.avg_wage. If it's from LaborMarket, it might be float.
        # We assume float input for market data for now, convert to pennies.
        avg_market_wage_float = market_snapshot.labor.avg_wage if hasattr(market_snapshot, "labor") else 0.0
        avg_market_wage = int(avg_market_wage_float * 100)

        if avg_market_wage > 0:
            state.market_wage_history.append(avg_market_wage)

        if state.shadow_reservation_wage_pennies <= 0:
            state.shadow_reservation_wage_pennies = state.current_wage_pennies if state.is_employed else state.expected_wage_pennies

        if state.is_employed:
            target = max(state.current_wage_pennies, state.shadow_reservation_wage_pennies)
            # Decay logic using float intermediate
            new_shadow = (state.shadow_reservation_wage_pennies * SHADOW_WAGE_DECAY) + (target * SHADOW_WAGE_TARGET_WEIGHT)
            state.shadow_reservation_wage_pennies = int(new_shadow)
        else:
            state.shadow_reservation_wage_pennies = int(state.shadow_reservation_wage_pennies * (1.0 - SHADOW_WAGE_UNEMPLOYED_DECAY))

            # Config min wage is now int pennies
            min_wage = config.household_min_wage_demand if hasattr(config, 'household_min_wage_demand') else 0

            if state.shadow_reservation_wage_pennies < min_wage:
                state.shadow_reservation_wage_pennies = min_wage

    def _plan_housing(self, state: EconStateDTO, market_snapshot: Any, current_tick: int) -> Optional[HousingActionDTO]:
        # Logic from DecisionUnit housing part
        if state.is_homeless or current_tick % HOUSING_CHECK_FREQUENCY == 0:
            class StateWrapper:
                def __init__(self, e_state):
                    self.econ_state = e_state

            wrapper = StateWrapper(state)

            housing_snap = market_snapshot.housing if hasattr(market_snapshot, "housing") else None

            if housing_snap:
                request = HousingDecisionRequestDTO(
                    household_state=wrapper,
                    housing_market_snapshot=housing_snap,
                    outstanding_debt_payments=0.0
                )

                decision = self.housing_planner.evaluate_housing_options(request)

                if decision['decision_type'] == "INITIATE_PURCHASE":
                    state.housing_target_mode = "BUY"
                    return HousingActionDTO(
                        action_type="INITIATE_PURCHASE",
                        property_id=str(decision['target_property_id']),
                        offer_price=int(decision['offer_price']), # Pennies
                        down_payment_amount=int(decision.get('down_payment_amount', 0.0)) # Pennies
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
        config: Any = None
    ) -> BudgetPlan:
        # 1. Total Wealth = Cash (int pennies)
        total_cash = state.wallet.get_balance(DEFAULT_CURRENCY)
        allocations: Dict[str, int] = {}
        spent = 0
        final_orders: List[Order] = []

        # 2. Allocate for Needs (Survival first)
        for need in needs:
            if need.need_id == "survival":
                # Estimate food cost.
                food_price_float = config.default_food_price_estimate if config else DEFAULT_FOOD_PRICE_ESTIMATE
                goods_market = getattr(market_snapshot, "goods", {})

                target_item = "basic_food"
                m = goods_market.get("basic_food")
                if not m:
                     m = goods_market.get("food")
                     target_item = "food" if m else "basic_food"

                if m:
                    # MarketSnapshotDTO uses GoodsMarketUnitDTO which has avg_price
                    food_price_float = getattr(m, "avg_price", food_price_float) or getattr(m, "current_price", food_price_float)

                # Convert allocation config (dollars) to pennies
                # Note: DEFAULT_SURVIVAL_BUDGET in this file is still 50.0 float.
                # If config is present, it's int pennies. If not, we use default * 100.
                if config:
                    amount_to_allocate_pennies = config.survival_budget_allocation
                else:
                    amount_to_allocate_pennies = int(DEFAULT_SURVIVAL_BUDGET * 100)

                allocated_cash = 0

                if total_cash - spent >= amount_to_allocate_pennies:
                    allocated_cash = amount_to_allocate_pennies
                else:
                    allocated_cash = max(0, total_cash - spent)

                allocations["food"] = allocated_cash
                spent += allocated_cash

                # Create Order for Food
                if allocated_cash > 0 and food_price_float > 0:
                    # Qty = Total Pennies / (Price Float * 100)
                    # Or: Qty = (Total Pennies / 100) / Price Float
                    qty = (allocated_cash / 100.0) / food_price_float

                    agent_id = getattr(state.wallet, "owner_id", None)
                    if agent_id:
                        order = Order(
                            agent_id=agent_id,
                            side="BUY",
                            item_id=target_item,
                            quantity=qty,
                            price_limit=food_price_float * 1.1, # 10% buffer
                            market_id="goods_market"
                        )
                        final_orders.append(order)

        # 3. Allocate for Abstract Plan (AI Orders)
        for order in abstract_plan:
            if order.side == "BUY":
                # Cost in pennies = Qty * Price * 100
                cost_float = order.quantity * order.price_limit
                cost_pennies = int(cost_float * 100)

                if total_cash - spent >= cost_pennies:
                    item_type = "investment" if "stock" in order.item_id else "goods"
                    allocations[item_type] = allocations.get(item_type, 0) + cost_pennies
                    spent += cost_pennies
                    final_orders.append(order)
            elif order.side == "SELL":
                final_orders.append(order)

        return BudgetPlan(
            allocations=allocations,
            discretionary_spending=max(0, total_cash - spent),
            orders=final_orders
        )
