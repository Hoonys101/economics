from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import logging
import math
from simulation.models import Order, Transaction
from simulation.components.state.firm_state_models import SalesState
from simulation.dtos.sales_dtos import SalesPostAskContextDTO, SalesMarketingContextDTO, MarketingAdjustmentResultDTO
from modules.system.api import MarketContextDTO, DEFAULT_CURRENCY
from modules.firm.api import ISalesEngine, DynamicPricingResultDTO
if TYPE_CHECKING:
    from modules.simulation.dtos.api import FirmConfigDTO
logger = logging.getLogger(__name__)

class SalesEngine(ISalesEngine):
    """
    Stateless Engine for Sales operations.
    Handles pricing, marketing, and order generation.
    MIGRATION: Uses integer pennies.
    """

    def post_ask(self, state: SalesState, context: SalesPostAskContextDTO) -> Order:
        """
        Posts an ask order to the market.
        Validates quantity against inventory.
        """
        actual_quantity = min(context.quantity, context.inventory_quantity)
        # Mutation removed for statelessness. Orchestrator must update last_prices.
        return Order(agent_id=context.firm_id, side='SELL', item_id=context.item_id, quantity=actual_quantity, price_pennies=context.price_pennies, price_limit=context.price_pennies / 100.0, market_id=context.market_id, brand_info=context.brand_snapshot, currency=DEFAULT_CURRENCY)

    def adjust_marketing_budget(self, state: SalesState, market_context: MarketContextDTO, revenue_this_turn: int, last_revenue: int=0, last_marketing_spend: int=0) -> MarketingAdjustmentResultDTO:
        """
        Adjusts marketing budget based on ROI or simple heuristic.
        Returns the calculated new budget in a DTO (pennies).
        """
        new_rate = state.marketing_budget_rate
        if last_marketing_spend > 0:
            revenue_delta = revenue_this_turn - last_revenue
            roi = revenue_delta / last_marketing_spend
            if roi > 1.5 and state.brand_awareness < 0.9:
                new_rate *= 1.1
            elif roi < 0.8:
                new_rate *= 0.9
        target_budget = revenue_this_turn * new_rate
        current_budget = float(state.marketing_budget_pennies)
        new_budget = current_budget * 0.8 + target_budget * 0.2
        return MarketingAdjustmentResultDTO(new_budget=int(new_budget), new_marketing_rate=new_rate)

    def generate_marketing_transaction(self, state: SalesState, context: SalesMarketingContextDTO) -> Optional[Transaction]:
        """
        Generates marketing spend transaction.
        """
        budget = state.marketing_budget_pennies
        if budget > 0 and context.wallet_balance >= budget and context.government_id:
            return Transaction(buyer_id=context.firm_id, seller_id=context.government_id, item_id='marketing', quantity=1.0, price=budget / 100.0, market_id='system', transaction_type='marketing', time=context.current_time, currency=DEFAULT_CURRENCY, total_pennies=budget)
        return None

    def check_and_apply_dynamic_pricing(self, state: SalesState, orders: List[Order], current_time: int, config: Optional[FirmConfigDTO]=None, unit_cost_estimator: Optional[Any]=None) -> DynamicPricingResultDTO:
        """
        Overrides prices in orders if dynamic pricing logic dictates.
        WO-157: Applies dynamic pricing discounts to stale inventory.
        Returns new orders list and price updates.
        """
        # Default result (no changes)
        price_updates: Dict[str, int] = {}
        new_orders = list(orders) # Create copy to avoid mutation if we were just modifying list, but we are returning new list

        if not config:
            return DynamicPricingResultDTO(orders=new_orders, price_updates=price_updates)

        sale_timeout = config.sale_timeout_ticks
        reduction_factor = config.dynamic_price_reduction_factor
        from dataclasses import replace

        for i, order in enumerate(new_orders):
            if not hasattr(order, 'item_id') or not order.item_id:
                continue
            side = getattr(order, 'side', getattr(order, 'order_type', None))
            if side == 'SELL':
                item_id = order.item_id
                last_sale = state.inventory_last_sale_tick.get(item_id, 0)
                if current_time - last_sale > sale_timeout:
                    # Original price is float price_limit or price
                    original_price_limit = getattr(order, 'price_limit', getattr(order, 'price', 0.0))

                    # Discount logic works on float price limit
                    discounted_price = original_price_limit * reduction_factor
                    final_price = discounted_price

                    if unit_cost_estimator:
                        # unit_cost_estimator returns int pennies
                        unit_cost_pennies = unit_cost_estimator(item_id)
                        unit_cost_float = unit_cost_pennies / 100.0
                        final_price = max(discounted_price, unit_cost_float)

                    # New Price Pennies
                    final_price_pennies = int(final_price * 100)
                    original_price_pennies = getattr(order, 'price_pennies', int(original_price_limit * 100))

                    if final_price_pennies < original_price_pennies:
                        new_order = replace(order, price_limit=final_price, price_pennies=final_price_pennies)
                        new_orders[i] = new_order
                        price_updates[item_id] = final_price_pennies

        return DynamicPricingResultDTO(orders=new_orders, price_updates=price_updates)