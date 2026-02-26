from typing import List
import random
from simulation.models import Order
from simulation.decisions.household.api import LaborContext
from modules.system.api import DEFAULT_CURRENCY
from modules.common.enums import IndustryDomain

class LaborManager:
    """
    Manages Labor decisions (Quit, Job Search, Reservation Wage).
    Refactored from AIDrivenHouseholdDecisionEngine.
    """

    def decide_labor(self, context: LaborContext) -> List[Order]:
        orders = []
        household = context.household
        config = context.config
        market_data = context.market_data
        action_vector = context.action_vector
        current_time = context.current_time
        logger = context.logger
        labor_market_info = market_data.get('goods_market', {}).get('labor', {})
        market_avg_wage = labor_market_info.get('avg_wage', config.labor_market_min_wage)
        best_market_offer = labor_market_info.get('best_wage_offer', 0.0)
        if household.is_employed:
            if hasattr(action_vector, 'job_mobility_aggressiveness'):
                agg_mobility = action_vector.job_mobility_aggressiveness
            else:
                agg_mobility = 0.5
            quit_threshold = config.job_quit_threshold_base - agg_mobility
            current_wage = getattr(household, 'current_wage', None)
            if current_wage is None and hasattr(household, 'current_wage_pennies'):
                current_wage = household.current_wage_pennies / 100.0
            if current_wage is None:
                current_wage = 0.0
            if market_avg_wage > current_wage * quit_threshold or best_market_offer > current_wage * quit_threshold:
                if random.random() < config.job_quit_prob_base + agg_mobility * config.job_quit_prob_scale:
                    orders.append(Order(agent_id=household.id, side='QUIT', item_id='labor', quantity=0.0, price_pennies=int(0.0 * 100), price_limit=0.0, market_id='labor'))
        if not household.is_employed:
            food_inventory = household.inventory.get('basic_food', 0.0)
            food_price = market_data.get('goods_market', {}).get('basic_food_avg_traded_price', 10.0)
            if food_price <= 0:
                food_price = 10.0
            household_assets = household.assets
            if isinstance(household_assets, dict):
                household_assets = household_assets.get(DEFAULT_CURRENCY, 0.0)
            else:
                household_assets = float(household_assets)
            survival_days = food_inventory + household_assets / food_price
            critical_turns = getattr(config, 'survival_critical_turns', 5)
            is_panic = False
            if survival_days < critical_turns:
                is_panic = True
                reservation_wage = 0.0
                if logger:
                    logger.info(f'PANIC_MODE | Household {household.id} desperate. Survival Days: {survival_days:.1f}. Wage: 0.0', extra={'tick': current_time, 'agent_id': household.id, 'tags': ['labor_panic']})
            else:
                reservation_wage = market_avg_wage * household.wage_modifier
            labor_market_info = market_data.get('goods_market', {}).get('labor', {})
            market_avg_wage = labor_market_info.get('avg_wage', config.labor_market_min_wage)
            best_market_offer = labor_market_info.get('best_wage_offer', 0.0)
            effective_offer = best_market_offer if best_market_offer > 0 else market_avg_wage
            wage_floor = reservation_wage
            if not is_panic and effective_offer < wage_floor:
                if logger:
                    logger.info(f'RESERVATION_WAGE | Household {household.id} refused labor. Offer: {effective_offer:.2f} < Floor: {wage_floor:.2f}', extra={'tick': current_time, 'agent_id': household.id, 'tags': ['labor_refusal']})
            else:
                # Prepare Brand Info for Utility-Based Matching
                if hasattr(household, 'agent_data'):
                    agent_data = household.agent_data
                elif hasattr(household, 'get_agent_data'):
                    agent_data = household.get_agent_data()
                else:
                    agent_data = {}

                # Convert major string to enum if needed
                major_val = getattr(household, 'major', 'GENERAL')
                if isinstance(major_val, str):
                    try:
                        major_enum = IndustryDomain(major_val)
                    except ValueError:
                        major_enum = IndustryDomain.GENERAL
                else:
                    major_enum = major_val

                brand_info = {
                    'labor_skill': agent_data.get('labor_skill', 1.0),
                    'education_level': agent_data.get('education_level', 0),
                    'aptitude': agent_data.get('aptitude', 0.5),
                    'market_insight': agent_data.get('market_insight', 0.5),
                    'major': major_val
                }

                orders.append(Order(
                    agent_id=household.id,
                    side='SELL',
                    item_id='labor',
                    quantity=1.0,
                    price_pennies=int(reservation_wage * 100),
                    price_limit=reservation_wage,
                    market_id='labor',
                    major=major_enum,
                    brand_info=brand_info
                ))
        return orders