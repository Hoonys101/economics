from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import logging
import copy
from modules.household.api import IConsumptionEngine, ConsumptionInputDTO, ConsumptionOutputDTO
from modules.household.dtos import EconStateDTO, BioStateDTO, SocialStateDTO
from modules.simulation.dtos.api import HouseholdConfigDTO
from simulation.dtos import LeisureEffectDTO
from simulation.models import Order
from modules.system.api import DEFAULT_CURRENCY
logger = logging.getLogger(__name__)
DEFAULT_FOOD_PRICE = 10.0
DEFAULT_FOOD_UTILITY = 20.0
PRICE_LIMIT_MULTIPLIER = 1.1

class ConsumptionEngine(IConsumptionEngine):
    """
    Stateless engine responsible for executing consumption from inventory,
    generating market orders based on budget, and handling panic selling.
    Logic migrated from ConsumptionManager and DecisionUnit.
    """

    def generate_orders(self, input_dto: ConsumptionInputDTO) -> ConsumptionOutputDTO:
        econ_state = input_dto.econ_state
        bio_state = input_dto.bio_state
        budget_plan = input_dto.budget_plan
        market_snapshot = input_dto.market_snapshot
        config = input_dto.config
        current_tick = input_dto.current_tick
        stress_scenario_config = input_dto.stress_scenario_config
        new_econ_state = econ_state.copy()
        new_bio_state = bio_state.copy()
        orders: List[Order] = []
        if stress_scenario_config and stress_scenario_config.is_active and (stress_scenario_config.scenario_name == 'deflation'):
            threshold = config.panic_selling_asset_threshold
            assets_val = new_econ_state.wallet.get_balance(DEFAULT_CURRENCY)
            if assets_val < threshold:
                for firm_id, share in new_econ_state.portfolio.holdings.items():
                    if share.quantity > 0:
                        stock_order = Order(agent_id=new_econ_state.portfolio.owner_id, side='SELL', item_id=f'stock_{firm_id}', quantity=share.quantity, price_pennies=int(0.0 * 100), price_limit=0.0, market_id='stock_market')
                        orders.append(stock_order)
        survival_need = new_bio_state.needs.get('survival', 0.0)
        food_inventory = new_econ_state.inventory.get('basic_food', 0.0) + new_econ_state.inventory.get('food', 0.0)
        if survival_need > 0 and food_inventory >= 1.0:
            if new_econ_state.inventory.get('basic_food', 0.0) >= 1.0:
                new_econ_state.inventory['basic_food'] -= 1.0
            else:
                new_econ_state.inventory['food'] -= 1.0
            utility = config.food_consumption_utility if config else DEFAULT_FOOD_UTILITY
            new_bio_state.needs['survival'] = max(0.0, survival_need - utility)
        orders.extend(budget_plan.orders)
        if stress_scenario_config and stress_scenario_config.is_active and (stress_scenario_config.scenario_name == 'phase29_depression'):
            multiplier = stress_scenario_config.demand_shock_multiplier
            if multiplier is not None:
                for order in orders:
                    if order.side == 'BUY' and hasattr(order, 'item_id') and (order.item_id not in ['labor', 'loan']):
                        if not order.item_id.startswith('stock_'):
                            order.quantity *= multiplier
        new_durable_assets = []
        for asset in new_econ_state.durable_assets:
            # DTO Realignment: Use dot notation for DurableAssetDTO
            new_asset = asset.copy()
            new_asset.remaining_life -= 1
            if new_asset.remaining_life > 0:
                new_durable_assets.append(new_asset)
        new_econ_state.durable_assets = new_durable_assets
        return ConsumptionOutputDTO(econ_state=new_econ_state, bio_state=new_bio_state, orders=orders, social_state=None)

    def apply_leisure_effect(self, leisure_hours: float, consumed_items: Dict[str, float], social_state: SocialStateDTO, econ_state: EconStateDTO, bio_state: BioStateDTO, config: HouseholdConfigDTO) -> Tuple[SocialStateDTO, EconStateDTO, LeisureEffectDTO]:
        has_children = len(bio_state.children_ids) > 0
        has_education = consumed_items.get('education_service', 0.0) > 0
        has_luxury = consumed_items.get('luxury_food', 0.0) > 0 or consumed_items.get('clothing', 0.0) > 0
        leisure_type = 'SELF_DEV'
        if has_children and has_education:
            leisure_type = 'PARENTING'
        elif has_luxury:
            leisure_type = 'ENTERTAINMENT'
        new_social_state = copy.deepcopy(social_state)
        new_social_state.last_leisure_type = leisure_type
        leisure_coeffs = config.leisure_coeffs
        coeffs = leisure_coeffs.get(leisure_type, {})
        utility_per_hour = coeffs.get('utility_per_hour', 0.0)
        xp_gain_per_hour = coeffs.get('xp_gain_per_hour', 0.0)
        productivity_gain = coeffs.get('productivity_gain', 0.0)
        utility_gained = leisure_hours * utility_per_hour
        xp_gained = leisure_hours * xp_gain_per_hour
        prod_gained = leisure_hours * productivity_gain
        new_econ_state = copy.deepcopy(econ_state)
        if leisure_type == 'SELF_DEV' and prod_gained > 0:
            new_econ_state.labor_skill += prod_gained

        # Phase 4.1: Insight Boost from Education
        if 'education_service' in consumed_items and consumed_items['education_service'] > 0:
            new_econ_state.market_insight = min(1.0, new_econ_state.market_insight + 0.05)

        effect_dto = LeisureEffectDTO(leisure_type=leisure_type, leisure_hours=leisure_hours, utility_gained=utility_gained, xp_gained=xp_gained)
        return (new_social_state, new_econ_state, effect_dto)