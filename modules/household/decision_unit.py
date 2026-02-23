from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
import logging
from modules.household.api import IDecisionUnit, OrchestrationContextDTO
from modules.household.dtos import EconStateDTO
from simulation.dtos import StressScenarioConfig
from simulation.models import Order
from modules.market.housing_planner import HousingPlanner
from modules.housing.dtos import HousingDecisionRequestDTO, HousingPurchaseDecisionDTO, HousingRentalDecisionDTO, HousingStayDecisionDTO
if TYPE_CHECKING:
    from modules.simulation.dtos.api import HouseholdConfigDTO
logger = logging.getLogger(__name__)

class DecisionUnit(IDecisionUnit):
    """
    Stateless unit responsible for coordinating decision making.
    Wraps DecisionEngine and System 2 logic (Orchestration).
    """

    def __init__(self):
        self.housing_planner = HousingPlanner()

    def orchestrate_economic_decisions(self, state: EconStateDTO, context: OrchestrationContextDTO, initial_orders: List[Order]) -> Tuple[EconStateDTO, List[Order]]:
        """
        Refines orders and updates internal economic state.
        Includes System 2 Housing Logic and Shadow Wage Logic.
        Logic migrated from EconComponent.orchestrate_economic_decisions.
        """
        new_state = state.copy()
        refined_orders = list(initial_orders)

        # Use dot notation for DTO access
        market_snapshot = context.market_snapshot
        current_time = context.current_time
        config = context.config
        stress_scenario_config = context.stress_scenario_config
        household_state = context.household_state
        housing_system = context.housing_system

        if household_state.econ_state.is_homeless or current_time % 30 == 0:
            request = HousingDecisionRequestDTO(household_state=household_state, housing_market_snapshot=market_snapshot.housing, outstanding_debt_payments=0.0)
            decision = self.housing_planner.evaluate_housing_options(request)
            if decision['decision_type'] == 'INITIATE_PURCHASE':
                if housing_system and hasattr(housing_system, 'initiate_purchase'):
                    housing_system.initiate_purchase(decision, buyer_id=state.portfolio.owner_id)
                    new_state.housing_target_mode = 'BUY'
                else:
                    pass
            elif decision['decision_type'] == 'MAKE_RENTAL_OFFER':
                new_state.housing_target_mode = 'RENT'
            elif decision['decision_type'] == 'STAY':
                new_state.housing_target_mode = 'STAY'

        avg_market_wage = market_snapshot.labor.avg_wage
        if avg_market_wage > 0:
            new_state.market_wage_history.append(avg_market_wage)

        if new_state.shadow_reservation_wage_pennies <= 0:
            new_state.shadow_reservation_wage_pennies = new_state.current_wage_pennies if new_state.is_employed else new_state.expected_wage_pennies

        if new_state.is_employed:
            target = max(new_state.current_wage_pennies, new_state.shadow_reservation_wage_pennies)
            new_state.shadow_reservation_wage_pennies = int(new_state.shadow_reservation_wage_pennies * 0.95 + target * 0.05)
        else:
            new_state.shadow_reservation_wage_pennies = int(new_state.shadow_reservation_wage_pennies * 0.98)
            min_wage_pennies = int(config.household_min_wage_demand * 100) if config.household_min_wage_demand < 100 else int(config.household_min_wage_demand)
            if new_state.shadow_reservation_wage_pennies < min_wage_pennies:
                new_state.shadow_reservation_wage_pennies = min_wage_pennies

        if stress_scenario_config and stress_scenario_config.is_active and (stress_scenario_config.scenario_name == 'deflation'):
            threshold = config.panic_selling_asset_threshold
            # Check assets via wallet (Legacy compat for DecisionUnit logic relying on float assets)
            # DTO has .assets property which returns dict.
            # Original code: new_state.assets < threshold. new_state.assets returns Dict[Currency, int].
            # This comparison < int is invalid.
            # Fix: Use wallet balance.
            assets_val = new_state.wallet.get_balance('USD') # Default currency
            if assets_val < threshold:
                for firm_id, share in new_state.portfolio.holdings.items():
                    if share.quantity > 0:
                        stock_order = Order(agent_id=state.portfolio.owner_id, side='SELL', item_id=f'stock_{firm_id}', quantity=share.quantity, price_pennies=int(0.0 * 100), price_limit=0.0, market_id='stock_market')
                        refined_orders.append(stock_order)

        if stress_scenario_config and stress_scenario_config.is_active and (stress_scenario_config.scenario_name == 'phase29_depression'):
            multiplier = stress_scenario_config.demand_shock_multiplier
            if multiplier is not None:
                for order in refined_orders:
                    if order.side == 'BUY' and hasattr(order, 'item_id') and (order.item_id not in ['labor', 'loan']):
                        if not order.item_id.startswith('stock_'):
                            order.quantity *= multiplier

        for order in refined_orders:
            if order.side == 'SELL' and (getattr(order, 'item_id', '') == 'labor' or order.market_id == 'labor'):
                new_state.last_labor_offer_tick = current_time
        return (new_state, refined_orders)
