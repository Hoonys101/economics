from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from simulation.firms import Firm
    from simulation.dtos.config_dtos import FirmConfigDTO
    from simulation.markets.order_book_market import OrderBookMarket

from simulation.models import Order

class SalesDepartment:
    """Handles the sales and marketing logic for a firm."""

    def __init__(self, firm: Firm, config: FirmConfigDTO):
        self.firm = firm
        self.config = config

    def post_ask(self, item_id: str, price: float, quantity: float, market: OrderBookMarket, current_tick: int) -> Order:
        """
        판매 주문을 생성하고 시장에 제출합니다.
        Brand Metadata를 자동으로 주입합니다.
        """
        # 1. 브랜드 정보 스냅샷
        brand_snapshot = {
            "brand_awareness": self.firm.brand_manager.brand_awareness,
            "perceived_quality": self.firm.brand_manager.perceived_quality,
            "quality": self.firm.inventory_quality.get(item_id, 1.0), # Phase 15: Physical Quality
        }

        # 2. 주문 생성 (brand_info 자동 주입)
        order = Order(
            agent_id=self.firm.id,
            side="SELL",
            item_id=item_id,
            quantity=quantity,
            price_limit=price,
            market_id=market.id,
            brand_info=brand_snapshot  # <-- Critical Injection
        )

        # 3. 시장에 제출
        market.place_order(order, current_tick)

        self.firm.logger.debug(
            f"FIRM_POST_ASK | Firm {self.firm.id} posted SELL order for {quantity:.1f} {item_id} @ {price:.2f} with brand_info",
            extra={"agent_id": self.firm.id, "tick": current_tick, "brand_awareness": brand_snapshot["brand_awareness"]}
        )

        return order

    def adjust_marketing_budget(self) -> None:
        """Adjust marketing budget rate based on ROI."""
        from modules.system.api import DEFAULT_CURRENCY

        delta_spend = self.firm.marketing_budget  # Current tick spend

        # Helper to safely get revenue
        def get_rev(val):
            if isinstance(val, dict):
                return val.get(DEFAULT_CURRENCY, 0.0)
            return float(val)

        current_revenue = get_rev(self.firm.finance.revenue_this_turn)
        last_revenue = get_rev(self.firm.finance.last_revenue)

        # Skip first tick or zero previous spend
        # Note: We use last_marketing_spend from PREVIOUS tick to calculate ROI of THAT spend.
        # But we also need to avoid division by zero.
        if delta_spend <= 0 or self.firm.finance.last_marketing_spend <= 0:
            self.firm.finance.last_revenue = current_revenue
            self.firm.finance.last_marketing_spend = self.firm.marketing_budget
            return

        delta_revenue = current_revenue - last_revenue
        efficiency = delta_revenue / self.firm.finance.last_marketing_spend

        # Decision Rules
        saturation_level = self.config.brand_awareness_saturation
        high_eff_threshold = self.config.marketing_efficiency_high_threshold
        low_eff_threshold = self.config.marketing_efficiency_low_threshold
        min_rate = self.config.marketing_budget_rate_min
        max_rate = self.config.marketing_budget_rate_max

        if self.firm.brand_manager.brand_awareness >= saturation_level:
            pass  # Maintain (Saturation)
        elif efficiency > high_eff_threshold:
            self.firm.marketing_budget_rate = min(max_rate, self.firm.marketing_budget_rate * 1.1)
        elif efficiency < low_eff_threshold:
            self.firm.marketing_budget_rate = max(min_rate, self.firm.marketing_budget_rate * 0.9)

        # Update tracking
        self.firm.finance.last_revenue = current_revenue
        self.firm.finance.last_marketing_spend = self.firm.marketing_budget

    def set_price(self, item_id: str, price: float) -> None:
        """Sets the price for a specific item."""
        self.firm.last_prices[item_id] = price

    def check_and_apply_dynamic_pricing(self, orders: List[Order], current_tick: int) -> None:
        """
        WO-157: Applies dynamic pricing discounts to stale inventory.
        Modifies orders in-place.
        """
        sale_timeout = getattr(self.config, 'sale_timeout_ticks', 20)
        reduction_factor = getattr(self.config, 'dynamic_price_reduction_factor', 0.95)
        from dataclasses import replace

        for i, order in enumerate(orders):
            # Check if order is a goods order (has item_id)
            if not hasattr(order, "item_id"):
                continue

            # Alias check for backward compatibility if side/order_type usage is mixed
            side = getattr(order, "side", getattr(order, "order_type", None))

            if side == "SELL":
                item_id = order.item_id
                last_sale = self.firm.inventory_last_sale_tick.get(item_id, 0)

                # Check Staleness
                if (current_tick - last_sale) > sale_timeout:
                    # Apply Discount
                    original_price = getattr(order, "price_limit", getattr(order, "price", 0.0))
                    discounted_price = original_price * reduction_factor

                    # Check Cost Floor
                    unit_cost = self.firm.finance.get_estimated_unit_cost(item_id)
                    final_price = max(discounted_price, unit_cost)

                    # Apply if lower
                    if final_price < original_price:
                        # order.price = final_price # Frozen
                        new_order = replace(order, price_limit=final_price)
                        orders[i] = new_order

                        # Update Firm's price memory
                        self.firm.last_prices[item_id] = final_price

                        self.firm.logger.info(
                            f"DYNAMIC_PRICING | Stale inventory {item_id}. "
                            f"Reduced price from {original_price:.2f} to {final_price:.2f} (Cost: {unit_cost:.2f})"
                        )
