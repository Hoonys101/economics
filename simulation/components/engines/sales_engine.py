from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import logging
import math
from dataclasses import replace

from simulation.models import Order, Transaction
from simulation.components.state.firm_state_models import SalesState
from simulation.dtos.sales_dtos import SalesPostAskContextDTO, SalesMarketingContextDTO, MarketingAdjustmentResultDTO
from modules.system.api import MarketContextDTO, DEFAULT_CURRENCY
from modules.firm.api import (
    ISalesEngine, ISalesDepartment, DynamicPricingResultDTO,
    SalesContextDTO, SalesIntentDTO, AgentID
)
from modules.firm.constants import DEFAULT_PRICE

if TYPE_CHECKING:
    from modules.simulation.dtos.api import FirmConfigDTO

logger = logging.getLogger(__name__)

class SalesEngine(ISalesEngine, ISalesDepartment):
    """
    Stateless Engine for Sales operations.
    Handles pricing, marketing, and order generation.
    MIGRATION: Uses integer pennies.
    """

    def decide_pricing(self, context: SalesContextDTO) -> SalesIntentDTO:
        """
        Pure function: SalesContextDTO -> SalesIntentDTO.
        Decides pricing, generates orders, and sets marketing budget.
        """
        price_adjustments: Dict[str, int] = {}
        sales_orders: List[Order] = []

        # 1. Generate Base Orders (Sell Everything Strategy)
        for item_id, quantity in context.inventory_to_sell.items():
            if quantity <= 0: continue

            price_pennies = context.current_prices.get(item_id, DEFAULT_PRICE) # Default if missing

            # Construct Brand Snapshot
            brand_snapshot = {
                "brand_awareness": context.brand_awareness,
                "perceived_quality": context.perceived_quality,
                "quality": context.inventory_quality.get(item_id, 1.0)
            }

            # Use correct market_id (usually matches item_id for goods)
            market_id = item_id

            order = Order(
                agent_id=context.firm_id,
                side='SELL',
                item_id=item_id,
                quantity=quantity,
                price_pennies=price_pennies,
                price_limit=price_pennies / 100.0,
                market_id=market_id,
                brand_info=brand_snapshot,
                currency=DEFAULT_CURRENCY
            )
            sales_orders.append(order)

        # 2. Apply Dynamic Pricing (Discounting stale inventory)
        sale_timeout = context.sale_timeout_ticks
        reduction_factor = context.dynamic_price_reduction_factor

        final_orders = []
        for order in sales_orders:
            item_id = order.item_id
            last_sale = context.inventory_last_sale_tick.get(item_id, 0)

            if context.tick - last_sale > sale_timeout:
                # Discount
                original_price_pennies = order.price_pennies
                discounted_pennies = int(original_price_pennies * reduction_factor)

                final_price_pennies = max(1, discounted_pennies) # Ensure positive price

                if final_price_pennies < original_price_pennies:
                    # Update Order
                    new_order = replace(order,
                        price_pennies=final_price_pennies,
                        price_limit=final_price_pennies / 100.0
                    )
                    final_orders.append(new_order)
                    price_adjustments[item_id] = final_price_pennies
                else:
                    final_orders.append(order)
            else:
                final_orders.append(order)

        # 3. Calculate Marketing Budget
        # Uses last_revenue_pennies (T-1) as proxy for performance
        new_rate = context.marketing_budget_rate
        last_spend = context.last_marketing_spend_pennies

        # Heuristic: If we spent money and got revenue, check ROI
        # Using simplified ROI logic here as we lack T-2 revenue for delta
        if last_spend > 0:
            revenue = context.last_revenue_pennies
            roi = revenue / last_spend

            if roi > 2.0 and context.brand_awareness < 0.9:
                new_rate *= 1.1
            elif roi < 1.0:
                new_rate *= 0.9

        target_budget = context.last_revenue_pennies * new_rate
        # Smoothing (80% old budget + 20% new target)
        # Note: current budget is unknown?
        # We can use last_spend as current budget proxy or
        # assume firm state manages smoothing.
        # But decide_pricing is determining the budget for THIS tick.
        # Let's return the calculated amount.

        # Smoothing logic usually requires "current set budget" vs "last actual spend".
        # context.last_marketing_spend_pennies is "actual spend".
        # We can assume last_spend is the baseline.

        new_budget = last_spend * 0.8 + target_budget * 0.2

        return SalesIntentDTO(
            price_adjustments=price_adjustments,
            sales_orders=final_orders,
            marketing_spend_pennies=int(new_budget),
            new_marketing_budget_rate=new_rate
        )

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
