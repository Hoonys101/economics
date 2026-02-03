from typing import List, Optional, Dict, Any
import logging
from simulation.models import Order
from simulation.dtos import DecisionContext, FirmStateDTO, FirmConfigDTO
from simulation.decisions.firm.api import OperationsPlanDTO
from modules.system.api import DEFAULT_CURRENCY

logger = logging.getLogger(__name__)

class ProductionStrategy:
    def formulate_plan(self, context: DecisionContext, capital_aggressiveness: float, rd_aggressiveness: float, guidance: Dict[str, Any]) -> OperationsPlanDTO:
        firm = context.state
        config = context.config
        market_data = context.market_data

        # Helper map for goods data
        goods_map = {g['id']: g for g in context.goods_data}

        orders = []

        # 0. Production Target Adjustment
        target_order = self._manage_production_target(firm, config)
        if target_order:
            orders.append(target_order)

        # 0. Procurement Channel (Raw Materials)
        procurement_orders = self._manage_procurement(firm, market_data, config, goods_map)
        orders.extend(procurement_orders)

        # Phase 21: Automation Channel
        auto_orders = self._manage_automation(firm, capital_aggressiveness, guidance, context.current_time, config)
        orders.extend(auto_orders)

        # 1. R&D Channel (Innovation)
        # Apply logic from CorporateManager: "if guidance.get("rd_intensity", 0.0) > 0.1: rd_agg = max(rd_agg, 0.5)"
        effective_rd_agg = rd_aggressiveness
        if guidance.get("rd_intensity", 0.0) > 0.1:
             effective_rd_agg = max(effective_rd_agg, 0.5)

        rd_order = self._manage_r_and_d(firm, effective_rd_agg, context.current_time, config)
        if rd_order:
            orders.append(rd_order)

        # 2. Capital Channel (CAPEX)
        capex_order = self._manage_capex(firm, capital_aggressiveness, context.current_time, config)
        if capex_order:
            orders.append(capex_order)

        return OperationsPlanDTO(orders=orders)

    def _manage_procurement(self, firm: FirmStateDTO, market_data: Dict[str, Any], config: FirmConfigDTO, goods_map: Dict[str, Any]) -> List[Order]:
        """
        WO-030: Manage Raw Material Procurement.
        """
        orders = []
        # Access goods_map instead of config_module.GOODS
        good_info = goods_map.get(firm.production.specialization, {})
        input_config = good_info.get("inputs", {})

        if not input_config:
            return orders

        target_production = firm.production.production_target

        for mat, req_per_unit in input_config.items():
            needed = target_production * req_per_unit
            current = firm.production.input_inventory.get(mat, 0.0)
            deficit = needed - current

            if deficit > 0:
                mat_market_data = market_data.get("goods_market", {})
                last_price_key = f"{mat}_avg_traded_price"
                fallback_price_key = f"{mat}_current_sell_price"

                last_price = mat_market_data.get(last_price_key, 0.0)
                if last_price <= 0:
                     last_price = mat_market_data.get(fallback_price_key, 0.0)
                if last_price <= 0:
                     mat_info = goods_map.get(mat, {})
                     last_price = mat_info.get("initial_price", 10.0)

                bid_price = last_price * 1.05
                orders.append(Order(agent_id=firm.id, side="BUY", item_id=mat, quantity=deficit, price_limit=bid_price, market_id=mat))

        return orders

    def _manage_automation(self, firm: FirmStateDTO, aggressiveness: float, guidance: Dict[str, Any], current_time: int, config: FirmConfigDTO) -> List[Order]:
        """
        Phase 21: Automation Investment.
        """
        orders = []
        target_a = guidance.get("target_automation", firm.production.automation_level)
        current_a = firm.production.automation_level

        if current_a >= target_a:
            return orders

        gap = target_a - current_a
        cost_per_pct = config.automation_cost_per_pct
        cost = cost_per_pct * (gap * 100.0)

        safety_margin = config.firm_safety_margin
        current_assets_raw = firm.finance.balance
        current_assets = current_assets_raw
        if isinstance(current_assets_raw, dict):
            current_assets = current_assets_raw.get(DEFAULT_CURRENCY, 0.0)

        investable_cash = max(0.0, current_assets - safety_margin)

        budget = investable_cash * (aggressiveness * 0.5)
        actual_spend = min(cost, budget)

        if actual_spend < 100.0:
            return orders

        # Generate Internal Order
        orders.append(Order(agent_id=firm.id, side="INVEST_AUTOMATION", item_id="internal", quantity=actual_spend, price_limit=0.0, market_id="internal"))

        # WO-044-Track-B: Automation Tax
        automation_tax_rate = config.automation_tax_rate
        tax_amount = actual_spend * automation_tax_rate

        if tax_amount > 0:
            orders.append(Order(agent_id=firm.id, side="PAY_TAX", item_id="automation_tax", quantity=tax_amount, price_limit=0.0, market_id="internal"))

        return orders

    def _manage_r_and_d(self, firm: FirmStateDTO, aggressiveness: float, current_time: int, config: FirmConfigDTO) -> Optional[Order]:
        """
        Innovation Physics.
        """
        if aggressiveness <= 0.1:
            return None

        current_revenue_raw = firm.finance.revenue_this_turn
        current_revenue = current_revenue_raw
        if isinstance(current_revenue_raw, dict):
            current_revenue = current_revenue_raw.get(DEFAULT_CURRENCY, 0.0)

        current_assets_raw = firm.finance.balance
        current_assets = current_assets_raw
        if isinstance(current_assets_raw, dict):
            current_assets = current_assets_raw.get(DEFAULT_CURRENCY, 0.0)

        revenue_base = max(current_revenue, current_assets * 0.05)
        rd_budget_rate = aggressiveness * 0.20
        budget = revenue_base * rd_budget_rate

        safety_margin = config.firm_safety_margin
        investable_cash = max(0.0, current_assets - safety_margin)

        if investable_cash < budget:
            budget = investable_cash * 0.5

        if budget < 10.0:
            return None

        return Order(agent_id=firm.id, side="INVEST_RD", item_id="internal", quantity=budget, price_limit=0.0, market_id="internal")

    def _manage_capex(self, firm: FirmStateDTO, aggressiveness: float, current_time: int, config: FirmConfigDTO) -> Optional[Order]:
        """
        Capacity Expansion.
        """
        if aggressiveness <= 0.2:
            return None

        safety_margin = config.firm_safety_margin
        current_assets_raw = firm.finance.balance
        current_assets = current_assets_raw
        if isinstance(current_assets_raw, dict):
            current_assets = current_assets_raw.get(DEFAULT_CURRENCY, 0.0)

        investable_cash = max(0.0, current_assets - safety_margin)

        budget = investable_cash * (aggressiveness * 0.5)

        if budget < 100.0:
            return None

        return Order(agent_id=firm.id, side="INVEST_CAPEX", item_id="internal", quantity=budget, price_limit=0.0, market_id="internal")

    def _manage_production_target(self, firm: FirmStateDTO, config: FirmConfigDTO) -> Optional[Order]:
        """
        Adjust Production Target based on Inventory Levels.
        """
        item = firm.production.specialization
        current_inventory = firm.production.inventory.get(item, 0.0)
        target = firm.production.production_target

        overstock_threshold = config.overstock_threshold
        understock_threshold = config.understock_threshold
        adj_factor = config.production_adjustment_factor
        min_target = config.firm_min_production_target
        max_target = config.firm_max_production_target

        new_target = target
        if current_inventory > target * overstock_threshold:
            new_target = target * (1.0 - adj_factor)
            new_target = max(min_target, new_target)
        elif current_inventory < target * understock_threshold:
            new_target = target * (1.0 + adj_factor)
            new_target = min(max_target, new_target)

        if new_target != target:
            return Order(agent_id=firm.id, side="SET_TARGET", item_id="internal", quantity=new_target, price_limit=0.0, market_id="internal")

        return None
