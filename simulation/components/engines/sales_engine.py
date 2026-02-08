from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import logging
import math
from simulation.models import Order, Transaction
from simulation.components.state.firm_state_models import SalesState
from modules.system.api import MarketContextDTO, DEFAULT_CURRENCY

if TYPE_CHECKING:
    from simulation.dtos.config_dtos import FirmConfigDTO
    from simulation.markets.order_book_market import OrderBookMarket

logger = logging.getLogger(__name__)

class SalesEngine:
    """
    Stateless Engine for Sales operations.
    Handles pricing, marketing, and order generation.
    """

    def post_ask(
        self,
        state: SalesState,
        firm_id: int,
        item_id: str,
        price: float,
        quantity: float,
        market: OrderBookMarket,
        current_tick: int,
        inventory_quantity: float,
        brand_snapshot: Optional[Dict[str, Any]] = None
    ) -> Order:
        """
        Posts an ask order to the market.
        Validates quantity against inventory.
        """
        # Ensure we don't sell more than we have
        actual_quantity = min(quantity, inventory_quantity)

        # Log pricing
        state.last_prices[item_id] = price

        return Order(
            agent_id=firm_id,
            side="SELL",
            item_id=item_id,
            quantity=actual_quantity,
            price_limit=price,
            market_id=market.id,
            brand_info=brand_snapshot,
            currency=DEFAULT_CURRENCY
        )

    def adjust_marketing_budget(
        self,
        state: SalesState,
        market_context: MarketContextDTO,
        revenue_this_turn: float # Total revenue in primary currency
    ) -> None:
        """
        Adjusts marketing budget based on ROI or simple heuristic.
        """
        # Simple heuristic: % of revenue
        target_budget = revenue_this_turn * state.marketing_budget_rate

        # Smoothing
        state.marketing_budget = (state.marketing_budget * 0.8) + (target_budget * 0.2)

    def generate_marketing_transaction(
        self,
        state: SalesState,
        firm_id: int,
        wallet_balance: float, # Primary currency balance
        government: Any,
        current_time: int
    ) -> Optional[Transaction]:
        """
        Generates marketing spend transaction.
        """
        budget = state.marketing_budget
        if budget > 0 and wallet_balance >= budget:
            return Transaction(
                buyer_id=firm_id,
                seller_id=government.id,
                item_id="marketing",
                quantity=1.0,
                price=budget,
                market_id="system",
                transaction_type="marketing",
                time=current_time,
                currency=DEFAULT_CURRENCY
            )
        return None

    def check_and_apply_dynamic_pricing(
        self,
        state: SalesState,
        orders: List[Order],
        current_time: int,
        config: Optional[FirmConfigDTO] = None,
        unit_cost_estimator: Optional[Any] = None
    ) -> None:
        """
        Overrides prices in orders if dynamic pricing logic dictates.
        WO-157: Applies dynamic pricing discounts to stale inventory.
        """
        if not config:
            return

        sale_timeout = config.sale_timeout_ticks
        reduction_factor = config.dynamic_price_reduction_factor
        from dataclasses import replace

        for i, order in enumerate(orders):
            # Check if order is a goods order (has item_id)
            if not hasattr(order, "item_id") or not order.item_id:
                continue

            # Alias check for backward compatibility
            side = getattr(order, "side", getattr(order, "order_type", None))

            if side == "SELL":
                item_id = order.item_id
                last_sale = state.inventory_last_sale_tick.get(item_id, 0)

                # Check Staleness
                if (current_time - last_sale) > sale_timeout:
                    # Apply Discount
                    original_price = getattr(order, "price_limit", getattr(order, "price", 0.0))
                    discounted_price = original_price * reduction_factor

                    # Check Cost Floor if estimator provided
                    final_price = discounted_price
                    if unit_cost_estimator:
                        unit_cost = unit_cost_estimator(item_id)
                        final_price = max(discounted_price, unit_cost)

                    # Apply if lower
                    if final_price < original_price:
                        new_order = replace(order, price_limit=final_price)
                        orders[i] = new_order

                        # Update price memory
                        state.last_prices[item_id] = final_price
