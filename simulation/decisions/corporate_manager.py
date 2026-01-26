from __future__ import annotations
from typing import List, Optional, Any, Dict
import logging
import random

from simulation.models import Order, StockOrder
from simulation.schemas import FirmActionVector
from simulation.dtos import DecisionContext, FirmStateDTO, FirmConfigDTO
from simulation.ai.firm_system2_planner import FirmSystem2Planner
from simulation.markets.stock_market import StockMarket

logger = logging.getLogger(__name__)

class CorporateManager:
    """
    CEO Module (WO-027).
    Translates the 6-channel Aggressiveness Vector (Strategy) into concrete Actions (Tactics).
    Owned by AIDrivenFirmDecisionEngine.
    Refactored for DTO Purity Gate (WO-114).
    """

    def __init__(self, config_module: Any, logger: Optional[logging.Logger] = None):
        self.config_module = config_module
        self.logger = logger if logger else logging.getLogger(__name__)
        self.system2_planner: Optional[FirmSystem2Planner] = None

    def realize_ceo_actions(
        self,
        firm: FirmStateDTO,
        context: DecisionContext,
        action_vector: FirmActionVector
    ) -> List[Order]:
        """
        Main entry point. Orchestrates all channel executions using pure DTOs.
        Returns a list of Orders (External and Internal).
        """
        orders: List[Order] = []
        config: FirmConfigDTO = context.config

        # Helper map for goods data
        goods_map = {g['id']: g for g in context.goods_data}

        # Phase 21: System 2 Strategic Guidance
        if self.system2_planner is None:
             self.system2_planner = FirmSystem2Planner(None, self.config_module)

        guidance = self.system2_planner.project_future(context.current_time, context.market_data, firm)

        # 0. Production Target Adjustment (Restored Logic)
        target_order = self._manage_production_target(firm, config)
        if target_order:
            orders.append(target_order)

        # 0. Procurement Channel (Raw Materials) - WO-030
        procurement_orders = self._manage_procurement(firm, context.market_data, config, goods_map)
        orders.extend(procurement_orders)

        # Phase 21: Automation Channel
        auto_orders = self._manage_automation(firm, action_vector.capital_aggressiveness, guidance, context.current_time, config)
        orders.extend(auto_orders)

        # 1. R&D Channel (Innovation)
        rd_agg = action_vector.rd_aggressiveness
        if guidance.get("rd_intensity", 0.0) > 0.1:
             rd_agg = max(rd_agg, 0.5)

        rd_order = self._manage_r_and_d(firm, rd_agg, context.current_time, config)
        if rd_order:
            orders.append(rd_order)

        # 2. Capital Channel (CAPEX)
        capex_agg = action_vector.capital_aggressiveness
        capex_order = self._manage_capex(firm, capex_agg, context.current_time, config)
        if capex_order:
            orders.append(capex_order)

        # 3. Dividend Channel
        div_order = self._manage_dividends(firm, action_vector.dividend_aggressiveness, config)
        if div_order:
            orders.append(div_order)

        # 4. Debt Channel (Leverage)
        debt_orders = self._manage_debt(firm, action_vector.debt_aggressiveness, context.market_data)
        orders.extend(debt_orders)

        # 5. Pricing Channel (Sales)
        pricing_orders = self._manage_pricing(firm, action_vector.sales_aggressiveness, context.market_data, context.current_time, config, goods_map)
        orders.extend(pricing_orders)

        # 6. Hiring Channel (Employment)
        hiring_orders = self._manage_hiring(firm, action_vector.hiring_aggressiveness, context.market_data, config)
        orders.extend(hiring_orders)

        # 7. Secondary Offering (SEO)
        seo_order = self._attempt_secondary_offering(firm, context, config)
        if seo_order:
            orders.append(seo_order)

        return orders

    def _attempt_secondary_offering(self, firm: FirmStateDTO, context: DecisionContext, config: FirmConfigDTO) -> Optional[StockOrder]:
        """Sell treasury shares to raise capital when cash is low."""
        startup_cost = config.startup_cost
        trigger_ratio = config.seo_trigger_ratio

        if firm.assets >= startup_cost * trigger_ratio:
            return None
        if firm.treasury_shares <= 0:
            return None

        # Use DTO
        market_snapshot = context.market_snapshot
        if not market_snapshot:
            return None

        max_sell_ratio = config.seo_max_sell_ratio
        sell_qty = min(firm.treasury_shares * max_sell_ratio, firm.treasury_shares)

        if sell_qty < 1.0:
            return None

        # Determine price (Market Price or Book Value)
        price = 0.0
        if market_snapshot:
             price = market_snapshot.prices.get(f"stock_{firm.id}", 0.0)

        if price is None or price <= 0:
            # Fallback to Book Value
            if firm.total_shares > 0:
                price = firm.assets / firm.total_shares
            else:
                price = 0.0

        if price <= 0:
            return None

        order = StockOrder(
            agent_id=firm.id,
            firm_id=firm.id,
            order_type="SELL",
            quantity=sell_qty,
            price=price,
            market_id="stock_market"
        )
        self.logger.info(f"SEO | Firm {firm.id} offering {sell_qty:.1f} shares at {price:.2f}")
        return order

    def _manage_procurement(self, firm: FirmStateDTO, market_data: Dict[str, Any], config: FirmConfigDTO, goods_map: Dict[str, Any]) -> List[Order]:
        """
        WO-030: Manage Raw Material Procurement.
        """
        orders = []
        # Access goods_map instead of config_module.GOODS
        good_info = goods_map.get(firm.specialization, {})
        input_config = good_info.get("inputs", {})

        if not input_config:
            return orders

        target_production = firm.production_target

        for mat, req_per_unit in input_config.items():
            needed = target_production * req_per_unit
            current = firm.input_inventory.get(mat, 0.0)
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
                orders.append(Order(firm.id, "BUY", mat, deficit, bid_price, mat))

        return orders

    def _manage_automation(self, firm: FirmStateDTO, aggressiveness: float, guidance: Dict[str, Any], current_time: int, config: FirmConfigDTO) -> List[Order]:
        """
        Phase 21: Automation Investment.
        """
        orders = []
        target_a = guidance.get("target_automation", firm.automation_level)
        current_a = firm.automation_level

        if current_a >= target_a:
            return orders

        gap = target_a - current_a
        cost_per_pct = config.automation_cost_per_pct
        cost = cost_per_pct * (gap * 100.0)

        safety_margin = config.firm_safety_margin
        investable_cash = max(0.0, firm.assets - safety_margin)

        budget = investable_cash * (aggressiveness * 0.5)
        actual_spend = min(cost, budget)

        if actual_spend < 100.0:
            return orders

        # Generate Internal Order
        orders.append(Order(firm.id, "INVEST_AUTOMATION", "internal", actual_spend, 0.0, "internal"))

        # WO-044-Track-B: Automation Tax
        automation_tax_rate = config.automation_tax_rate
        tax_amount = actual_spend * automation_tax_rate

        if tax_amount > 0:
            orders.append(Order(firm.id, "PAY_TAX", "automation_tax", tax_amount, 0.0, "internal"))

        return orders

    def _manage_r_and_d(self, firm: FirmStateDTO, aggressiveness: float, current_time: int, config: FirmConfigDTO) -> Optional[Order]:
        """
        Innovation Physics.
        """
        if aggressiveness <= 0.1:
            return None

        revenue_base = max(firm.revenue_this_turn, firm.assets * 0.05)
        rd_budget_rate = aggressiveness * 0.20
        budget = revenue_base * rd_budget_rate

        safety_margin = config.firm_safety_margin
        investable_cash = max(0.0, firm.assets - safety_margin)

        if investable_cash < budget:
            budget = investable_cash * 0.5

        if budget < 10.0:
            return None

        return Order(firm.id, "INVEST_RD", "internal", budget, 0.0, "internal")

    def _manage_capex(self, firm: FirmStateDTO, aggressiveness: float, current_time: int, config: FirmConfigDTO) -> Optional[Order]:
        """
        Capacity Expansion.
        """
        if aggressiveness <= 0.2:
            return None

        safety_margin = config.firm_safety_margin
        investable_cash = max(0.0, firm.assets - safety_margin)

        budget = investable_cash * (aggressiveness * 0.5)

        if budget < 100.0:
            return None

        return Order(firm.id, "INVEST_CAPEX", "internal", budget, 0.0, "internal")

    def _manage_dividends(self, firm: FirmStateDTO, aggressiveness: float, config: FirmConfigDTO) -> Optional[Order]:
        """
        Set Dividend Rate.
        """
        z_score = firm.altman_z_score
        z_score_threshold = config.altman_z_score_threshold
        loss_limit = config.dividend_suspension_loss_ticks

        is_distressed = (z_score < z_score_threshold) or (firm.consecutive_loss_turns >= loss_limit)

        if is_distressed:
            return Order(firm.id, "SET_DIVIDEND", "internal", 0.0, 0.0, "internal")

        base_rate = config.dividend_rate_min
        max_rate = config.dividend_rate_max
        new_rate = base_rate + (aggressiveness * (max_rate - base_rate))

        return Order(firm.id, "SET_DIVIDEND", "internal", new_rate, 0.0, "internal")

    def _manage_debt(self, firm: FirmStateDTO, aggressiveness: float, market_data: Dict) -> List[Order]:
        """
        Leverage Management.
        """
        orders = []
        target_leverage = aggressiveness * 2.0

        current_debt = 0.0
        debt_info = market_data.get("debt_data", {}).get(firm.id)
        if debt_info:
            current_debt = debt_info.get("total_principal", 0.0)

        current_assets = max(firm.assets, 1.0)
        current_leverage = current_debt / current_assets

        if current_leverage < target_leverage:
            desired_debt = current_assets * target_leverage
            borrow_amount = desired_debt - current_debt
            borrow_amount = min(borrow_amount, current_assets * 0.5)

            if borrow_amount > 100.0:
                orders.append(
                    Order(firm.id, "LOAN_REQUEST", "loan", borrow_amount, 0.10, "loan")
                )

        elif current_leverage > target_leverage:
            excess_debt = current_debt - (current_assets * target_leverage)
            repay_amount = min(excess_debt, firm.assets * 0.5)

            if repay_amount > 10.0 and current_debt > 0:
                 orders.append(
                    Order(firm.id, "REPAYMENT", "loan", repay_amount, 1.0, "loan")
                )

        return orders

    def _manage_pricing(self, firm: FirmStateDTO, aggressiveness: float, market_data: Dict, current_time: int, config: FirmConfigDTO, goods_map: Dict[str, Any]) -> List[Order]:
        """
        Sales Channel.
        """
        orders = []
        item_id = firm.specialization
        current_inventory = firm.inventory.get(item_id, 0)

        if current_inventory <= 0:
            return orders

        market_price = 0.0
        if item_id in market_data:
             market_price = market_data[item_id].get('avg_price', 0)
        if market_price <= 0:
             market_price = firm.price_history.get(item_id, 0)
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
        orders.append(Order(firm.id, "SET_PRICE", item_id, target_price, 0.0, "internal"))

        # 2. Market Order to sell
        qty = min(current_inventory, config.max_sell_quantity)

        # We generate a direct SELL order here.
        # Note: Previous logic called `firm.sales.post_ask` which might do more (logging, etc).
        # But we are in DTO mode. The Engine outputs Intent.

        # target_market check removed for DTO purity
        orders.append(Order(
             agent_id=firm.id,
             order_type="SELL",
             item_id=item_id,
             quantity=qty,
             price=target_price,
             market_id=item_id # Assumes market_id == item_id
        ))

        return orders

    def _manage_hiring(self, firm: FirmStateDTO, aggressiveness: float, market_data: Dict, config: FirmConfigDTO) -> List[Order]:
        """
        Hiring Channel.
        """
        orders = []
        target_inventory = firm.production_target
        current_inventory = firm.inventory.get(firm.specialization, 0)
        inventory_gap = target_inventory - current_inventory

        base_alpha = config.labor_alpha
        automation_reduction = config.automation_labor_reduction
        alpha_adjusted = base_alpha * (1.0 - (firm.automation_level * automation_reduction))
        beta_adjusted = 1.0 - alpha_adjusted

        capital = max(firm.capital_stock, 1.0)
        tfp = firm.productivity_factor

        if tfp <= 0: tfp = 1.0

        needed_labor_calc = 0.0
        if inventory_gap > 0:
            try:
                 term = inventory_gap / (tfp * (capital ** beta_adjusted))
                 needed_labor_calc = term ** (1.0 / alpha_adjusted)
            except Exception:
                 needed_labor_calc = 1.0
        else:
            needed_labor_calc = 0.0

        needed_labor = int(needed_labor_calc) + 1
        current_employees = len(firm.employees)

        # A. Firing Logic (Layoffs)
        if current_employees > needed_labor:
            excess = current_employees - needed_labor
            fire_count = min(excess, max(0, current_employees - 1))

            if fire_count > 0:
                # Identify candidates (FIFO from ID list)
                candidates = firm.employees[:fire_count]

                severance_weeks = config.severance_pay_weeks

                for emp_id in candidates:
                    # Get wage and skill from DTO
                    emp_data = firm.employees_data.get(emp_id, {})
                    wage = emp_data.get("wage", config.labor_market_min_wage)
                    skill = emp_data.get("skill", 1.0)

                    adjusted_wage = wage * skill
                    severance_pay = adjusted_wage * severance_weeks

                    # Generate FIRE order
                    orders.append(Order(
                        firm.id,
                        "FIRE",
                        "internal",
                        1,
                        severance_pay,
                        "internal",
                        target_agent_id=emp_id
                    ))

                return orders

        # B. Hiring Logic
        market_wage = config.labor_market_min_wage
        if "labor" in market_data and "avg_wage" in market_data["labor"]:
             market_wage = market_data["labor"]["avg_wage"]

        adjustment = -0.2 + (aggressiveness * 0.5)
        offer_wage = market_wage * (1.0 + adjustment)
        offer_wage = max(config.labor_market_min_wage, offer_wage)

        # Competitive Bidding Logic (Simplified from original due to DTO access limits or replicate it?)
        # We can replicate `_adjust_wage_for_vacancies` using DTO data.
        offer_wage = self._adjust_wage_for_vacancies(firm, offer_wage, needed_labor, market_data)

        to_hire = needed_labor - current_employees
        if to_hire > 0:
            for _ in range(to_hire):
                 orders.append(
                     Order(firm.id, "BUY", "labor", 1, offer_wage, "labor")
                 )

        return orders

    def _adjust_wage_for_vacancies(self, firm: FirmStateDTO, base_offer_wage: float, needed_labor: int, market_data: Dict) -> float:
        """
        WO-047-B: Competitive Bidding Logic (DTO version).
        """
        current_employees = len(firm.employees)
        vacancies = max(0, needed_labor - current_employees)
        
        if vacancies <= 0:
            return base_offer_wage

        # 1. Solvency Check
        # Need liabilities. DTO doesn't have it explicitly.
        # But we can get it from market_data debt info.
        total_liabilities = 0.0
        debt_info = market_data.get("debt_data", {}).get(firm.id)
        if debt_info:
            total_liabilities = debt_info.get("total_principal", 0.0)

        if total_liabilities > 0:
            solvency_ratio = firm.assets / total_liabilities
            if solvency_ratio < 1.5:
                return base_offer_wage
        
        # 2. Wage Bill Cap
        wage_bill = 0.0
        if firm.employees_data:
            wage_bill = sum(e['wage'] for e in firm.employees_data.values())

        if wage_bill > 0 and firm.assets < wage_bill * 2: 
             return base_offer_wage

        # 3. Calculate Increase
        increase_rate = min(0.05, 0.01 * vacancies)
        new_wage = base_offer_wage * (1.0 + increase_rate)

        # 4. Absolute Ceiling
        max_affordable = firm.assets / (current_employees + vacancies + 1)
        if new_wage > max_affordable:
            new_wage = max(base_offer_wage, max_affordable)

        return max(base_offer_wage, new_wage)

    def _manage_production_target(self, firm: FirmStateDTO, config: FirmConfigDTO) -> Optional[Order]:
        """
        Adjust Production Target based on Inventory Levels.
        """
        item = firm.specialization
        current_inventory = firm.inventory.get(item, 0.0)
        target = firm.production_target

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
            return Order(firm.id, "SET_TARGET", "internal", new_target, 0.0, "internal")

        return None
