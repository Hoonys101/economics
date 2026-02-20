from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any
import logging
from dataclasses import replace
from simulation.orchestration.api import IPhaseStrategy
from simulation.dtos.api import SimulationState, DecisionInputDTO
from simulation.models import Order
from simulation.systems.api import CommerceContext
from simulation.orchestration.utils import prepare_market_data
from simulation.orchestration.factories import DecisionInputFactory, MarketSnapshotFactory
from simulation.markets.order_book_market import OrderBookMarket
from simulation.core_agents import Household
from simulation.systems.perception_system import PerceptionSystem

if TYPE_CHECKING:
    from simulation.world_state import WorldState
logger = logging.getLogger(__name__)

class Phase1_Decision(IPhaseStrategy):

    def __init__(self, world_state: WorldState):
        self.world_state = world_state
        self.input_factory = DecisionInputFactory()
        self.snapshot_factory = MarketSnapshotFactory()
        self.perception_system = PerceptionSystem()

    def execute(self, state: SimulationState) -> SimulationState:
        self._snapshot_agent_pre_states(state)
        market_data = prepare_market_data(state)
        state.market_data = market_data
        market_snapshot = self.snapshot_factory.create_snapshot(state)

        # Update perception system with the raw truth
        self.perception_system.update(market_snapshot)

        base_input_dto = self.input_factory.create_decision_input(state, self.world_state, market_snapshot)
        self._dispatch_firm_decisions(state, base_input_dto)
        self._dispatch_household_decisions(state, base_input_dto)
        self._plan_commerce(state, market_data)
        return state

    def _snapshot_agent_pre_states(self, state: SimulationState):
        for f in state.firms:
            if f.is_active:
                f.pre_state_snapshot = f.get_agent_data()
        for h in state.households:
            if h._bio_state.is_active:
                h.pre_state_snapshot = h.get_agent_data()

    def _dispatch_firm_decisions(self, state: SimulationState, base_input_dto: DecisionInputDTO):
        firm_pre_states = {}
        for firm in state.firms:
            if not firm.is_active:
                continue
            if hasattr(firm.decision_engine, 'ai_engine') and firm.decision_engine.ai_engine:
                pre_strategic_state = firm.decision_engine.ai_engine._get_strategic_state(firm.get_agent_data(), state.market_data)
                pre_tactical_state = firm.decision_engine.ai_engine._get_tactical_state(firm.decision_engine.ai_engine.chosen_intention, firm.get_agent_data(), state.market_data)
                firm_pre_states[firm.id] = {'pre_strategic_state': pre_strategic_state, 'pre_tactical_state': pre_tactical_state, 'chosen_intention': firm.decision_engine.ai_engine.chosen_intention, 'chosen_tactic': firm.decision_engine.ai_engine.last_chosen_tactic}
            # Phase 4.1: Perceptual Filters
            market_insight = firm.market_insight if hasattr(firm, 'market_insight') else 0.5
            filtered_snapshot = self.perception_system.apply_filter(market_insight, base_input_dto.market_snapshot)
            filtered_policy = self.perception_system.apply_policy_filter(market_insight, base_input_dto.government_policy)

            firm_input = replace(
                base_input_dto,
                market_snapshot=filtered_snapshot,
                government_policy=filtered_policy,
                stress_scenario_config=self.world_state.stress_scenario_config
            )
            decision_output = firm.make_decision(firm_input)
            if hasattr(decision_output, 'orders'):
                firm_orders = decision_output.orders
            else:
                firm_orders, action_vector = decision_output
            for order in firm_orders:
                target_market = state.markets.get(order.market_id)
                if target_market:
                    new_txs = target_market.place_order(order, state.time)
                    if new_txs:
                        state.transactions.extend(new_txs)
        state.firm_pre_states = firm_pre_states

    def _dispatch_household_decisions(self, state: SimulationState, base_input_dto: DecisionInputDTO):
        household_pre_states = {}
        household_time_allocation = {}
        for household in state.households:
            if not household._bio_state.is_active:
                continue
            if hasattr(household.decision_engine, 'ai_engine') and household.decision_engine.ai_engine:
                pre_strategic_state = household.decision_engine.ai_engine._get_strategic_state(household.get_agent_data(), state.market_data)
                household_pre_states[household.id] = {'pre_strategic_state': pre_strategic_state}
            # Phase 4.1: Perceptual Filters
            market_insight = household._econ_state.market_insight if hasattr(household, '_econ_state') else 0.5
            filtered_snapshot = self.perception_system.apply_filter(market_insight, base_input_dto.market_snapshot)
            filtered_policy = self.perception_system.apply_policy_filter(market_insight, base_input_dto.government_policy)

            household_input = replace(
                base_input_dto,
                market_snapshot=filtered_snapshot,
                government_policy=filtered_policy,
                stress_scenario_config=self.world_state.stress_scenario_config,
                macro_context=base_input_dto.macro_context
            )
            decision_output = household.make_decision(household_input)
            if hasattr(decision_output, 'orders'):
                household_orders = decision_output.orders
                metadata = decision_output.metadata
                if hasattr(metadata, 'work_aggressiveness'):
                    work_aggressiveness = metadata.work_aggressiveness
                else:
                    work_aggressiveness = 0.5
            else:
                household_orders, action_vector = decision_output
                if hasattr(action_vector, 'work_aggressiveness'):
                    work_aggressiveness = action_vector.work_aggressiveness
                else:
                    work_aggressiveness = 0.5
            max_work_hours = state.config_module.MAX_WORK_HOURS
            shopping_hours = getattr(state.config_module, 'SHOPPING_HOURS', 2.0)
            hours_per_tick = getattr(state.config_module, 'HOURS_PER_TICK', 24.0)
            work_hours = work_aggressiveness * max_work_hours
            leisure_hours = max(0.0, hours_per_tick - work_hours - shopping_hours)
            household_time_allocation[household.id] = leisure_hours
            for order in household_orders:
                self._process_household_order(state, household, order, state.market_data)
        state.household_pre_states = household_pre_states
        state.household_time_allocation = household_time_allocation

    def _process_household_order(self, state: SimulationState, household: Household, order: Order, market_data: Dict[str, Any]):
        if hasattr(order, 'item_id') and order.item_id == 'basic_food' and (order.side == 'BUY'):
            deflationary_multiplier = getattr(state.config_module, 'DEFLATIONARY_PRESSURE_MULTIPLIER', None)
            if deflationary_multiplier is not None:
                current_price = market_data.get('basic_food_current_sell_price', 5.0)
                new_price = min(order.price_limit, max(0.1, current_price * float(deflationary_multiplier)))
                order = replace(order, price_limit=new_price, price_pennies=int(new_price * 100))
        if order.side == 'INVEST' and order.market_id == 'admin':
            if self.world_state.firm_system:
                self.world_state.firm_system.spawn_firm(state, household)
            else:
                state.logger.warning(f'SKIPPED_INVESTMENT | Agent {household.id} tried startup but firm_system missing.')
            return
        target_market_id = self._get_redirected_market(order)
        household_target_market = state.markets.get(target_market_id)
        if household_target_market:
            new_txs = household_target_market.place_order(order, state.time)
            if new_txs:
                state.transactions.extend(new_txs)

    def _get_redirected_market(self, order: Order) -> str:
        target_market_id = order.market_id
        if order.side in ['DEPOSIT', 'WITHDRAW', 'LOAN_REQUEST', 'REPAYMENT']:
            target_market_id = 'loan_market'
        elif hasattr(order, 'item_id') and order.item_id in ['deposit', 'currency']:
            target_market_id = 'loan_market'
        return target_market_id

    def _plan_commerce(self, state: SimulationState, market_data: Dict[str, Any]):
        current_vacancies = 0
        labor_market = state.markets.get('labor')
        if labor_market and isinstance(labor_market, OrderBookMarket):
            for item_orders in labor_market.buy_orders.values():
                for order in item_orders:
                    current_vacancies += order.quantity
        consumption_market_data = market_data.copy()
        consumption_market_data['job_vacancies'] = current_vacancies
        sales_tax_rate = getattr(state.config_module, 'SALES_TAX_RATE', 0.05)
        commerce_context: CommerceContext = {'households': state.households, 'agents': state.agents, 'breeding_planner': self.world_state.breeding_planner, 'household_time_allocation': state.household_time_allocation, 'market_data': consumption_market_data, 'config': state.config_module, 'time': state.time, 'government': state.primary_government, 'sales_tax_rate': sales_tax_rate}
        if self.world_state.commerce_system:
            planned_cons, commerce_txs = self.world_state.commerce_system.plan_consumption_and_leisure(commerce_context, self.world_state.stress_scenario_config)
            state.planned_consumption = planned_cons
            for tx in commerce_txs:
                if tx.transaction_type == 'PHASE23_MARKET_ORDER':
                    order = Order(agent_id=tx.buyer_id, side='BUY', item_id=tx.item_id, quantity=tx.quantity, price_pennies=int(tx.price * 100), price_limit=tx.price, market_id=tx.item_id)
                    market = state.markets.get(tx.item_id)
                    if market:
                        new_txs = market.place_order(order, state.time)
                        if new_txs:
                            state.transactions.extend(new_txs)
                else:
                    state.transactions.append(tx)
        return state