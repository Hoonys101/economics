from typing import List, Any, Optional, Tuple
import random
from simulation.models import Order
from simulation.decisions.household.api import ConsumptionContext
from modules.system.api import DEFAULT_CURRENCY
from simulation.schemas import HouseholdActionVector

class ConsumptionManager:
    """
    Manages consumption logic (Maslow, Utility, Veblen, Hoarding).
    Refactored from AIDrivenHouseholdDecisionEngine.
    """

    def check_survival_override(self, household: Any, config: Any, market_snapshot: Any, current_time: int, logger: Optional[Any]) -> Optional[Tuple[List[Order], HouseholdActionVector]]:
        """
        Phase 2: Survival Override.
        Checks if critical needs exceed threshold and triggers panic buying.
        """
        survival_need = household.needs.get('survival', 0)
        emergency_threshold = getattr(config, 'survival_need_emergency_threshold', 0.8)
        if not isinstance(emergency_threshold, (int, float)):
            emergency_threshold = 0.8
        if logger:
            logger.info(f"SURVIVAL_CHECK | Need: {survival_need}, Threshold: {emergency_threshold}, Food: {getattr(config, 'primary_survival_good_id', 'food')}")
        if survival_need > emergency_threshold:
            food_id = getattr(config, 'primary_survival_good_id', 'food')
            if not isinstance(food_id, str):
                food_id = 'food'
            ask_price = None
            if market_snapshot:
                if isinstance(market_snapshot, dict):
                    signals = market_snapshot.get('market_signals')
                else:
                    signals = getattr(market_snapshot, 'market_signals', None)
                if isinstance(signals, dict):
                    signal = signals.get(food_id)
                    if signal:
                        if hasattr(signal, 'best_ask') and signal.best_ask is not None:
                            ask_price = signal.best_ask
                        elif isinstance(signal, dict) and signal.get('best_ask') is not None:
                            ask_price = signal['best_ask']
                elif signals:
                    signal_dto = getattr(signals, food_id, None)
                    if signal_dto and getattr(signal_dto, 'best_ask', None) is not None:
                        ask_price = getattr(signal_dto, 'best_ask')
            if ask_price is not None:
                if isinstance(ask_price, dict) and 'amount' in ask_price:
                    ask_price = ask_price['amount']
                elif hasattr(ask_price, 'amount'):
                    ask_price = ask_price.amount
                household_assets = household.assets
                if isinstance(household_assets, dict):
                    household_assets = household_assets.get(DEFAULT_CURRENCY, 0.0)
                else:
                    household_assets = float(household_assets)
                if household_assets >= ask_price:
                    premium_pennies = getattr(config, 'survival_bid_premium', 20)
                    if not isinstance(premium_pennies, int):
                        premium_pennies = 20
                    bid_price = ask_price + premium_pennies
                    if logger:
                        logger.warning(f'SURVIVAL_OVERRIDE | Agent {household.id} critical need {survival_need:.2f}. Panic buying {food_id} at {bid_price:.2f}', extra={'agent_id': household.id, 'tick': current_time, 'tags': ['survival', 'override']})
                    survival_order = Order(agent_id=household.id, side='BUY', item_id=food_id, quantity=1.0, price_pennies=int(bid_price * 100), price_limit=bid_price, market_id=food_id)
                    return ([survival_order], HouseholdActionVector(work_aggressiveness=1.0))
        return None

    def decide_consumption(self, context: ConsumptionContext) -> List[Order]:
        orders = []
        household = context.household
        config = context.config
        market_data = context.market_data
        action_vector = context.action_vector
        savings_roi = context.savings_roi
        debt_penalty = context.debt_penalty
        stress_config = context.stress_config
        logger = context.logger
        goods_list = list(config.goods.keys())
        for item_id in goods_list:
            if item_id == 'consumer_goods':
                food_inventory = household.inventory.get('basic_food', 0.0)
                target_buffer = getattr(config, 'target_food_buffer_quantity', 5.0)
                if food_inventory < target_buffer:
                    continue
            if hasattr(household, 'durable_assets'):
                existing_durables = [a for a in household.durable_assets if a['item_id'] == item_id]
                has_inventory = household.inventory.get(item_id, 0.0) >= 1.0
                if existing_durables or has_inventory:
                    if random.random() < 0.95:
                        continue
            if hasattr(action_vector, 'consumption_aggressiveness'):
                agg_buy = action_vector.consumption_aggressiveness.get(item_id, 0.5)
            else:
                agg_buy = 0.5
            avg_price = market_data.get('goods_market', {}).get(f'{item_id}_current_sell_price', config.market_price_fallback)
            if not avg_price or avg_price <= 0:
                avg_price = config.market_price_fallback
            good_info = config.goods.get(item_id, {})
            max_need_value = 0.0
            utility_effects = good_info.get('utility_effects', {})
            for need_type in utility_effects.keys():
                nv = household.needs.get(need_type, 0.0)
                if nv > max_need_value:
                    max_need_value = nv
            demand_elasticity = getattr(household, 'demand_elasticity', 1.0)
            mwtp_multiplier = getattr(config, 'max_willingness_to_pay_multiplier', 2.5)
            perceived_price = household.perceived_prices.get(item_id, avg_price)
            max_affordable_price = mwtp_multiplier * perceived_price
            quantity_to_buy = 0.0
            if avg_price >= max_affordable_price:
                quantity_to_buy = 0.0
            else:
                price_ratio = avg_price / max_affordable_price
                quantity_to_buy = max_need_value * (1.0 - price_ratio) ** demand_elasticity
            if getattr(config, 'enable_vanity_system', False) and good_info.get('is_veblen', False):
                conformity = getattr(household, 'conformity', 0.5)
                max_affordable_price *= 1.0 + 0.5 * conformity
                if avg_price < max_affordable_price:
                    price_ratio = avg_price / max_affordable_price
                    quantity_to_buy = max_need_value * (1.0 - price_ratio) ** demand_elasticity
                    quantity_to_buy *= 1.0 + 0.2 * conformity
            household_assets = household.assets
            if isinstance(household_assets, dict):
                household_assets = household_assets.get(DEFAULT_CURRENCY, 0.0)
            else:
                household_assets = float(household_assets)
            budget_limit = household_assets * config.budget_limit_normal_ratio
            if max_need_value > config.budget_limit_urgent_need:
                budget_limit = household_assets * config.budget_limit_urgent_ratio

            # Apply Debt Constraint (Wave 6)
            # If debt_penalty < 1.0 (indicating stress), reduce the budget limit proportionally.
            if debt_penalty < 1.0:
                budget_limit *= debt_penalty

            bid_price = avg_price * 1.05
            if bid_price > max_affordable_price:
                bid_price = max_affordable_price
            bid_price = max(bid_price, avg_price)
            cost = quantity_to_buy * bid_price
            if cost > budget_limit:
                quantity_to_buy = budget_limit / bid_price
            if quantity_to_buy >= config.min_purchase_quantity:
                final_quantity = quantity_to_buy
                if good_info.get('is_durable', False):
                    final_quantity = max(1, int(quantity_to_buy))
                orders.append(Order(agent_id=household.id, side='BUY', item_id=item_id, quantity=final_quantity, price_pennies=int(bid_price * 100), price_limit=bid_price, market_id=item_id))
        return orders