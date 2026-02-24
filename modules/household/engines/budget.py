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
DESPERATION_THRESHOLD_TICKS = 20
DESPERATION_WAGE_DECAY = 0.95
HOUSING_CHECK_FREQUENCY = 30
DEFAULT_FOOD_PRICE_ESTIMATE = 10.0
DEFAULT_SURVIVAL_BUDGET_PENNIES = 5000 # 50.00
MARKET_ID_GOODS = 'goods_market'

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

        self._update_shadow_wage(new_econ_state, market_snapshot, config, current_tick)
        housing_action = self._plan_housing(new_econ_state, market_snapshot, current_tick)
        budget_plan = self._create_budget_plan(new_econ_state, prioritized_needs, abstract_plan, market_snapshot, config, input_dto=input_dto)

        return BudgetOutputDTO(econ_state=new_econ_state, budget_plan=budget_plan, housing_action=housing_action)

    def _update_shadow_wage(self, state: EconStateDTO, market_snapshot: Any, config: Any, current_tick: int):
        avg_market_wage_float = market_snapshot.labor.avg_wage if hasattr(market_snapshot, 'labor') else 0.0
        avg_market_wage = int(avg_market_wage_float * 100)

        if avg_market_wage > 0:
            state.market_wage_history.append(avg_market_wage)

        if state.shadow_reservation_wage_pennies <= 0:
            state.shadow_reservation_wage_pennies = state.current_wage_pennies if state.is_employed else state.expected_wage_pennies

        if state.is_employed:
            target = max(state.current_wage_pennies, state.shadow_reservation_wage_pennies)
            new_shadow = state.shadow_reservation_wage_pennies * SHADOW_WAGE_DECAY + target * SHADOW_WAGE_TARGET_WEIGHT
            state.shadow_reservation_wage_pennies = int(new_shadow)
        else:
            # Phase 4.2: Desperation Decay
            unemployment_duration = 0
            if state.last_fired_tick > 0:
                 unemployment_duration = current_tick - state.last_fired_tick

            decay_factor = 1.0 - SHADOW_WAGE_UNEMPLOYED_DECAY
            if unemployment_duration > DESPERATION_THRESHOLD_TICKS:
                 decay_factor = DESPERATION_WAGE_DECAY

            state.shadow_reservation_wage_pennies = int(state.shadow_reservation_wage_pennies * decay_factor)

            # Floor at 1 penny, regardless of min_wage config if desperate
            min_wage = config.household_min_wage_demand if hasattr(config, 'household_min_wage_demand') else 0

            if unemployment_duration > DESPERATION_THRESHOLD_TICKS:
                 # Desperation overrides min wage config, floor is 1 penny
                 min_wage = 1

            if state.shadow_reservation_wage_pennies < min_wage:
                state.shadow_reservation_wage_pennies = min_wage

    def _plan_housing(self, state: EconStateDTO, market_snapshot: Any, current_tick: int) -> Optional[HousingActionDTO]:
        if state.is_homeless or current_tick % HOUSING_CHECK_FREQUENCY == 0:
            # Create a wrapper to mimic legacy structure if needed by HousingPlanner
            # Assuming HousingDecisionRequestDTO expects an object with 'econ_state' attribute
            class StateWrapper:
                def __init__(self, e_state):
                    self.econ_state = e_state

            wrapper = StateWrapper(state)
            housing_snap = market_snapshot.housing if hasattr(market_snapshot, 'housing') else None

            if housing_snap:
                request = HousingDecisionRequestDTO(household_state=wrapper, housing_market_snapshot=housing_snap, outstanding_debt_payments=0.0)
                decision = self.housing_planner.evaluate_housing_options(request)

                if decision['decision_type'] == 'INITIATE_PURCHASE':
                    state.housing_target_mode = 'BUY'
                    return HousingActionDTO(
                        action_type='INITIATE_PURCHASE',
                        property_id=str(decision['target_property_id']),
                        offer_price=int(decision['offer_price']),
                        down_payment_amount=int(decision.get('down_payment_amount', 0.0))
                    )
                elif decision['decision_type'] == 'MAKE_RENTAL_OFFER':
                    state.housing_target_mode = 'RENT'
                    return HousingActionDTO(
                        action_type='MAKE_RENTAL_OFFER',
                        property_id=str(decision['target_property_id'])
                    )
                elif decision['decision_type'] == 'STAY':
                    state.housing_target_mode = 'STAY'
                    return HousingActionDTO(action_type='STAY')
        return None

    def _create_budget_plan(self, state: EconStateDTO, needs: List[PrioritizedNeed], abstract_plan: List[Any], market_snapshot: Any, config: Any=None, input_dto: Any=None) -> BudgetPlan:
        total_cash = state.wallet.get_balance(DEFAULT_CURRENCY)
        allocations: Dict[str, int] = {}
        spent = 0
        final_orders: List[Order] = []

        agent_id = getattr(input_dto, 'agent_id', None)
        if not agent_id:
            agent_id = getattr(state.wallet, 'owner_id', None)

        goods_market = getattr(market_snapshot, 'goods', {})

        for need in needs:
            if need.need_id == 'medical':
                 spent += self._handle_medical_need(allocations, final_orders, total_cash, spent, goods_market, agent_id)

            elif need.need_id == 'survival':
                 spent += self._handle_survival_need(allocations, final_orders, total_cash, spent, goods_market, config, agent_id)

        for order in abstract_plan:
            if order.side == 'BUY':
                cost_float = order.quantity * order.price_limit
                cost_pennies = int(cost_float * 100)
                if total_cash - spent >= cost_pennies:
                    item_type = 'investment' if 'stock' in order.item_id else 'goods'
                    allocations[item_type] = allocations.get(item_type, 0) + cost_pennies
                    spent += cost_pennies
                    final_orders.append(order)
            elif order.side == 'SELL':
                final_orders.append(order)

        return BudgetPlan(allocations=allocations, discretionary_spending=max(0, total_cash - spent), orders=final_orders)

    def _handle_medical_need(self, allocations: Dict[str, int], final_orders: List[Order], total_cash: int, spent: int, goods_market: Any, agent_id: Optional[int]) -> int:
        target_item = "medical_service"
        m = goods_market.get(target_item)

        # Default estimate (pennies)
        price_estimate = 10000.0
        if m:
            price_estimate = getattr(m, 'avg_price', price_estimate) or getattr(m, 'current_price', price_estimate)

        cost_pennies = int(price_estimate * 1.2) # 20% premium for urgency
        allocated_cash = min(max(0, total_cash - spent), cost_pennies)

        if allocated_cash > 0:
            allocations['medical'] = allocated_cash
            qty = 1.0

            if agent_id:
                price_limit = allocated_cash / 100.0
                order = Order(
                    agent_id=agent_id,
                    side='BUY',
                    item_id=target_item,
                    quantity=qty,
                    price_pennies=allocated_cash,
                    price_limit=price_limit,
                    market_id=MARKET_ID_GOODS
                )
                final_orders.append(order)
            return allocated_cash
        return 0

    def _handle_survival_need(self, allocations: Dict[str, int], final_orders: List[Order], total_cash: int, spent: int, goods_market: Any, config: Any, agent_id: Optional[int]) -> int:
        food_price_float = config.default_food_price_estimate if config else DEFAULT_FOOD_PRICE_ESTIMATE
        target_item = 'basic_food'
        m = goods_market.get('basic_food')
        if not m:
            m = goods_market.get('food')
            target_item = 'food' if m else 'basic_food'

        if m:
            food_price_float = getattr(m, 'avg_price', food_price_float) or getattr(m, 'current_price', food_price_float)

        if config:
            amount_to_allocate_pennies = config.survival_budget_allocation
        else:
            amount_to_allocate_pennies = DEFAULT_SURVIVAL_BUDGET_PENNIES

        allocated_cash = 0
        if total_cash - spent >= amount_to_allocate_pennies:
            allocated_cash = amount_to_allocate_pennies
        else:
            allocated_cash = max(0, total_cash - spent)

        allocations['food'] = allocated_cash

        if allocated_cash > 0 and food_price_float > 0:
            qty = allocated_cash / 100.0 / food_price_float
            if agent_id:
                order = Order(
                    agent_id=agent_id,
                    side='BUY',
                    item_id=target_item,
                    quantity=qty,
                    price_pennies=int(food_price_float * 1.1 * 100),
                    price_limit=food_price_float * 1.1,
                    market_id=MARKET_ID_GOODS
                )
                final_orders.append(order)
        return allocated_cash
