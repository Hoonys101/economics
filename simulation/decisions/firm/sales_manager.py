from typing import List, Dict, Any
import logging
from simulation.models import Order
from simulation.dtos import DecisionContext, FirmStateDTO, FirmConfigDTO
from simulation.decisions.firm.api import SalesPlanDTO

logger = logging.getLogger(__name__)

class SalesManager:
    def formulate_plan(self, context: DecisionContext, sales_aggressiveness: float) -> SalesPlanDTO:
        firm = context.state
        config = context.config
        market_data = context.market_data

        # Helper map for goods data
        goods_map = {g['id']: g for g in context.goods_data}

        orders = self._manage_pricing(firm, sales_aggressiveness, market_data, context.current_time, config, goods_map)

        return SalesPlanDTO(orders=orders)

    def _manage_pricing(self, firm: FirmStateDTO, aggressiveness: float, market_data: Dict, current_time: int, config: FirmConfigDTO, goods_map: Dict[str, Any]) -> List[Order]:
        """
        Sales Channel.
        """
        orders = []
        item_id = firm.production.specialization
        current_inventory = firm.production.inventory.get(item_id, 0)

        if current_inventory <= 0:
            return orders

        market_price = 0.0
        if item_id in market_data:
             market_price = market_data[item_id].get('avg_price', 0)
        if market_price <= 0:
             market_price = firm.sales.price_history.get(item_id, 0)
        if market_price <= 0:
             market_price = goods_map.get(item_id, {}).get("production_cost", 10.0)

        adjustment = (0.5 - aggressiveness) * 0.4
        target_price = market_price * (1.0 + adjustment)

        # Sales volume handling via DTO? DTO doesn't have last_sales_volume explicitly in root, but maybe we can infer?
        # FirmStateDTO doesn't have sales volume.
        # Fallback to 1.0 if not available.
        sales_vol = 1.0

        days_on_hand = current_inventory / sales_vol
        decay = max(0.5, 1.0 - (days_on_hand * 0.005))
        target_price *= decay

        target_price = max(target_price, 0.1)

        # 1. Internal Order to update price state
        orders.append(Order(agent_id=firm.id, side="SET_PRICE", item_id=item_id, quantity=0.0, price_limit=target_price, market_id="internal"))

        # 2. Market Order to sell
        qty = min(current_inventory, config.max_sell_quantity)

        # We generate a direct SELL order here.
        orders.append(Order(
             agent_id=firm.id,
             side="SELL",
             item_id=item_id,
             quantity=qty,
             price_limit=target_price,
             market_id=item_id # Assumes market_id == item_id
        ))

        return orders
