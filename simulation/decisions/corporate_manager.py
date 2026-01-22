from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Any, Dict
import logging
import random
import math

from simulation.models import Order, StockOrder
from simulation.schemas import FirmActionVector
from simulation.dtos import DecisionContext
from simulation.markets.stock_market import StockMarket
from simulation.dtos.firm_state_dto import FirmStateDTO

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

class CorporateManager:
    """
    CEO Module (WO-027).
    Translates the 6-channel Aggressiveness Vector (Strategy) into concrete Actions (Tactics).
    Owned by AIDrivenFirmDecisionEngine.
    Refactored for WO-107 (Stateless DTO).
    """

    def __init__(self, config_module: Any, logger: Optional[logging.Logger] = None):
        self.config_module = config_module
        self.logger = logger if logger else logging.getLogger(__name__)

    def realize_ceo_actions(
        self,
        firm_state: FirmStateDTO,
        context: DecisionContext,
        action_vector: FirmActionVector,
        guidance: Dict[str, Any]
    ) -> List[Order]:
        """
        Main entry point. Orchestrates all channel executions.
        """
        orders: List[Order] = []

        # 0. Procurement Channel (Raw Materials) - WO-030
        procurement_orders = self._manage_procurement(firm_state, context.market_data)
        orders.extend(procurement_orders)

        # Phase 21: Automation Channel (New)
        # Uses Capital Aggressiveness + System 2 Target
        self._manage_automation(firm_state, action_vector.capital_aggressiveness, guidance, context.current_time, orders)

        # 1. R&D Channel (Innovation)
        rd_agg = action_vector.rd_aggressiveness
        if guidance.get("rd_intensity", 0.0) > 0.1:
             rd_agg = max(rd_agg, 0.5) # Minimum effort if strategic priority

        self._manage_r_and_d(firm_state, rd_agg, context.current_time, orders)

        # 2. Capital Channel (CAPEX - Physical Machines)
        capex_agg = action_vector.capital_aggressiveness
        self._manage_capex(firm_state, capex_agg, context.reflux_system, context.current_time, orders)

        # 3. Dividend Channel
        self._manage_dividends(firm_state, action_vector.dividend_aggressiveness, orders)

        # 4. Debt Channel (Leverage)
        debt_orders = self._manage_debt(firm_state, action_vector.debt_aggressiveness, context.market_data)
        orders.extend(debt_orders)

        # 5. Pricing Channel (Sales)
        self._manage_pricing(firm_state, action_vector.sales_aggressiveness, context.market_data, context.markets, context.current_time, orders)

        # 6. Hiring Channel (Employment)
        hiring_orders = self._manage_hiring(firm_state, action_vector.hiring_aggressiveness, context.market_data, orders)
        orders.extend(hiring_orders)

        # 7. Secondary Offering (SEO)
        seo_order = self._attempt_secondary_offering(firm_state, context)
        if seo_order:
            orders.append(seo_order)

        return orders

    def _attempt_secondary_offering(self, firm_state: FirmStateDTO, context: DecisionContext) -> Optional[StockOrder]:
        """Sell treasury shares to raise capital when cash is low."""
        startup_cost = getattr(self.config_module, "STARTUP_COST", 30000.0)
        trigger_ratio = getattr(self.config_module, "SEO_TRIGGER_RATIO", 0.5)

        if firm_state.assets >= startup_cost * trigger_ratio:
            return None
        if firm_state.treasury_shares <= 0:
            return None

        stock_market = context.markets.get("stock_market")
        if not stock_market or not isinstance(stock_market, StockMarket):
            return None

        max_sell_ratio = getattr(self.config_module, "SEO_MAX_SELL_RATIO", 0.10)
        sell_qty = min(firm_state.treasury_shares * max_sell_ratio, firm_state.treasury_shares)

        if sell_qty < 1.0:
            return None

        price = stock_market.get_stock_price(firm_state.id)
        if price is None or price <= 0:
            # Calculate BPS from DTO
            outstanding_shares = firm_state.total_shares - firm_state.treasury_shares
            net_assets = firm_state.assets - firm_state.total_debt # Simplified BPS (Cash - Debt) / Shares. Real BPS includes inventory/capital.
            # Real BPS: (Assets + InventoryVal + Capital) - Debt.
            # Inventory Value estimation:
            inv_val = 0.0
            for item, qty in firm_state.inventory.items():
                p = firm_state.last_prices.get(item, 10.0)
                inv_val += qty * p

            total_assets = firm_state.assets + inv_val + firm_state.capital_stock
            bps = max(0.0, total_assets - firm_state.total_debt) / outstanding_shares if outstanding_shares > 0 else 0.0
            price = bps

        if price <= 0:
            return None

        order = StockOrder(
            agent_id=firm_state.id,
            firm_id=firm_state.id,
            order_type="SELL",
            quantity=sell_qty,
            price=price
        )
        self.logger.info(f"SEO | Firm {firm_state.id} offering {sell_qty:.1f} shares at {price:.2f}")
        return order

    def _manage_procurement(self, firm_state: FirmStateDTO, market_data: Dict[str, Any]) -> List[Order]:
        """
        WO-030: Manage Raw Material Procurement.
        """
        orders = []
        input_config = self.config_module.GOODS.get(firm_state.specialization, {}).get("inputs", {})

        if not input_config:
            return orders

        target_production = firm_state.production_target

        for mat, req_per_unit in input_config.items():
            needed = target_production * req_per_unit
            current = firm_state.input_inventory.get(mat, 0.0)
            deficit = needed - current

            if deficit > 0:
                mat_market_data = market_data.get("goods_market", {})
                last_price_key = f"{mat}_avg_traded_price"
                fallback_price_key = f"{mat}_current_sell_price"

                last_price = mat_market_data.get(last_price_key, 0.0)
                if last_price <= 0:
                     last_price = mat_market_data.get(fallback_price_key, 0.0)
                if last_price <= 0:
                     last_price = self.config_module.GOODS.get(mat, {}).get("initial_price", 10.0)

                bid_price = last_price * 1.05
                orders.append(Order(firm_state.id, "BUY", mat, deficit, bid_price, mat))

        return orders

    def _manage_automation(self, firm_state: FirmStateDTO, aggressiveness: float, guidance: Dict[str, Any], current_time: int, orders: List[Order]) -> None:
        """
        Phase 21: Automation Investment.
        Emits INVEST_AUTOMATION internal order.
        """
        target_a = guidance.get("target_automation", firm_state.automation_level)
        current_a = firm_state.automation_level

        if current_a >= target_a:
            return

        gap = target_a - current_a
        cost_per_pct = getattr(self.config_module, "AUTOMATION_COST_PER_PCT", 1000.0)
        cost = cost_per_pct * (gap * 100.0)

        safety_margin = getattr(self.config_module, "FIRM_SAFETY_MARGIN", 2000.0)
        investable_cash = max(0.0, firm_state.assets - safety_margin)

        budget = investable_cash * (aggressiveness * 0.5)
        actual_spend = min(cost, budget)

        if actual_spend < 100.0:
            return

        # Emit Internal Order
        orders.append(Order(
            agent_id=firm_state.id,
            order_type="INVEST_AUTOMATION",
            item_id="automation",
            quantity=actual_spend,
            price=0.0,
            market_id="internal"
        ))

    def _manage_r_and_d(self, firm_state: FirmStateDTO, aggressiveness: float, current_time: int, orders: List[Order]) -> None:
        """
        Innovation Physics.
        Emits INVEST_RD internal order.
        """
        if aggressiveness <= 0.1:
            return

        revenue_base = max(firm_state.revenue_this_turn, firm_state.assets * 0.05)
        rd_budget_rate = aggressiveness * 0.20
        budget = revenue_base * rd_budget_rate

        safety_margin = getattr(self.config_module, "FIRM_SAFETY_MARGIN", 2000.0)
        investable_cash = max(0.0, firm_state.assets - safety_margin)

        if investable_cash < budget:
            budget = investable_cash * 0.5

        if budget < 10.0:
            return

        orders.append(Order(
            agent_id=firm_state.id,
            order_type="INVEST_RD",
            item_id="rd",
            quantity=budget,
            price=0.0,
            market_id="internal"
        ))

    def _manage_capex(self, firm_state: FirmStateDTO, aggressiveness: float, reflux_system: Any, current_time: int, orders: List[Order]) -> None:
        """
        Capacity Expansion.
        Emits INVEST_CAPEX internal order.
        """
        if aggressiveness <= 0.2:
            return

        safety_margin = getattr(self.config_module, "FIRM_SAFETY_MARGIN", 2000.0)
        investable_cash = max(0.0, firm_state.assets - safety_margin)

        budget = investable_cash * (aggressiveness * 0.5)

        if budget < 100.0:
            return

        orders.append(Order(
            agent_id=firm_state.id,
            order_type="INVEST_CAPEX",
            item_id="capex",
            quantity=budget,
            price=0.0,
            market_id="internal"
        ))

    def _manage_dividends(self, firm_state: FirmStateDTO, aggressiveness: float, orders: List[Order]) -> None:
        """
        Set Dividend Rate.
        Emits SET_DIVIDEND_RATE internal order.
        """
        # Calculate Z-Score roughly (simplified or moved to Firm?)
        # For simplicity, check consecutive losses which we have.
        # Ideally Firm should manage distress logic, but CorporateManager sets policy.
        # We can implement a simplified check or trust Firm to override/reject?
        # Let's check consecutive losses.
        loss_limit = getattr(self.config_module, "DIVIDEND_SUSPENSION_LOSS_TICKS", 3)

        # Simplified Z-Score check logic using DTO fields if possible
        # working_capital = firm_state.assets - firm_state.total_debt
        # total_assets = firm_state.assets + firm_state.capital_stock + inventory_val
        # ...
        # For now, rely on consecutive losses and a simple solvency check.

        is_distressed = (firm_state.consecutive_loss_turns >= loss_limit)

        rate = 0.0
        if not is_distressed:
            base_rate = getattr(self.config_module, "DIVIDEND_RATE_MIN", 0.1)
            max_rate = getattr(self.config_module, "DIVIDEND_RATE_MAX", 0.5)
            rate = base_rate + (aggressiveness * (max_rate - base_rate))

        orders.append(Order(
            agent_id=firm_state.id,
            order_type="SET_DIVIDEND_RATE",
            item_id="dividend_rate",
            quantity=0.0,
            price=rate, # Pass rate as price
            market_id="internal"
        ))

    def _manage_debt(self, firm_state: FirmStateDTO, aggressiveness: float, market_data: Dict) -> List[Order]:
        """
        Leverage Management.
        """
        orders = []
        target_leverage = aggressiveness * 2.0

        current_debt = firm_state.total_debt
        current_assets = max(firm_state.assets, 1.0)
        current_leverage = current_debt / current_assets

        if current_leverage < target_leverage:
            desired_debt = current_assets * target_leverage
            borrow_amount = desired_debt - current_debt
            borrow_amount = min(borrow_amount, current_assets * 0.5)

            if borrow_amount > 100.0:
                orders.append(
                    Order(firm_state.id, "LOAN_REQUEST", "loan", borrow_amount, 0.10, "loan")
                )

        elif current_leverage > target_leverage:
            excess_debt = current_debt - (current_assets * target_leverage)
            repay_amount = min(excess_debt, firm_state.assets * 0.5)

            if repay_amount > 10.0 and current_debt > 0:
                 orders.append(
                    Order(firm_state.id, "REPAYMENT", "loan", repay_amount, 1.0, "loan")
                )

        return orders

    def _manage_pricing(self, firm_state: FirmStateDTO, aggressiveness: float, market_data: Dict, markets: Dict, current_time: int, orders: List[Order]) -> None:
        """
        Sales Channel.
        Emits SET_PRICE and SELL orders.
        """
        item_id = firm_state.specialization
        current_inventory = firm_state.inventory.get(item_id, 0)

        if current_inventory <= 0:
            return

        market_price = 0.0
        if item_id in market_data:
             market_price = market_data[item_id].get('avg_price', 0)
        if market_price <= 0:
             market_price = firm_state.last_prices.get(item_id, 0)
        if market_price <= 0:
             market_price = self.config_module.GOODS.get(item_id, {}).get("production_cost", 10.0)

        adjustment = (0.5 - aggressiveness) * 0.4
        target_price = market_price * (1.0 + adjustment)

        sales_vol = firm_state.last_sales_volume
        if sales_vol <= 0: sales_vol = 1.0
        days_on_hand = current_inventory / sales_vol
        decay = max(0.5, 1.0 - (days_on_hand * 0.005))
        target_price *= decay

        target_price = max(target_price, 0.1)

        # Emit SET_PRICE
        orders.append(Order(
            agent_id=firm_state.id,
            order_type="SET_PRICE",
            item_id=item_id,
            quantity=0.0,
            price=target_price,
            market_id="internal"
        ))

        # Emit SELL order
        qty = min(current_inventory, self.config_module.MAX_SELL_QUANTITY)

        # Check if market exists to be safe, although we can't check market obj here easily if markets dict is just names?
        # context.markets contains Market objects.
        target_market = markets.get(item_id)
        if target_market:
            orders.append(Order(
                agent_id=firm_state.id,
                order_type="SELL",
                item_id=item_id,
                quantity=qty,
                price=target_price,
                market_id=item_id # Usually keyed by item_id
            ))

    def _manage_hiring(self, firm_state: FirmStateDTO, aggressiveness: float, market_data: Dict, orders: List[Order]) -> List[Order]:
        """
        Hiring Channel.
        """
        new_orders = [] # Local list to return hiring orders (BUY labor)

        target_inventory = firm_state.production_target
        current_inventory = firm_state.inventory.get(firm_state.specialization, 0)
        inventory_gap = target_inventory - current_inventory

        if inventory_gap <= 0:
            return []

        base_alpha = getattr(self.config_module, "LABOR_ALPHA", 0.7)
        automation_reduction = getattr(self.config_module, "AUTOMATION_LABOR_REDUCTION", 0.5)
        alpha_adjusted = base_alpha * (1.0 - (firm_state.automation_level * automation_reduction))
        beta_adjusted = 1.0 - alpha_adjusted

        capital = max(firm_state.capital_stock, 1.0)
        tfp = firm_state.productivity_factor
        if tfp <= 0: tfp = 1.0

        needed_labor_calc = 0.0
        try:
             term = inventory_gap / (tfp * (capital ** beta_adjusted))
             needed_labor_calc = term ** (1.0 / alpha_adjusted)
        except Exception:
             needed_labor_calc = 1.0

        needed_labor = int(needed_labor_calc) + 1
        current_employees = firm_state.employee_count

        # A. Firing Logic (Layoffs)
        if current_employees > needed_labor:
            excess = current_employees - needed_labor
            fire_count = min(excess, max(0, current_employees - 1))

            if fire_count > 0:
                # We need to pick employees to fire.
                # DTO has `employees` (List[int]).
                candidates = firm_state.employees[:fire_count]

                severance_weeks = getattr(self.config_module, "SEVERANCE_PAY_WEEKS", 4)

                for emp_id in candidates:
                    wage = firm_state.employee_wages.get(emp_id, self.config_module.LABOR_MARKET_MIN_WAGE)
                    # Skill is not in DTO map? `employee_wages` is actual wage, which typically includes skill premium?
                    # `Firm.hr.employee_wages` stores contract wage.
                    # Base logic used `emp.labor_skill`. DTO doesn't have per-employee skill.
                    # Simplified: Use contract wage * 1.0 (assuming average skill or contract accounts for it).
                    # Or assume severance based on contract wage is sufficient estimate.

                    severance_pay = wage * severance_weeks

                    # Emit FIRE order
                    # We pass severance amount as price? Or quantity?
                    # Use price for monetary amount.
                    orders.append(Order(
                        agent_id=firm_state.id,
                        order_type="FIRE",
                        item_id="labor",
                        quantity=0.0,
                        price=severance_pay, # Severance amount
                        market_id="internal",
                        # We need target_agent_id... Order class doesn't have it.
                        # We can overload item_id? "FIRE_{emp_id}"?
                        # Or rely on a separate mechanism?
                        # Order class allows us to define item_id.
                        # Let's use item_id = f"employee_{emp_id}"?
                        # Or just handle it in Firm.make_decision by parsing item_id.
                    ))
                    # Hack: Store emp_id in item_id for FIRE command
                    orders[-1].item_id = str(emp_id)

                return []

        # B. Hiring Logic
        market_wage = self.config_module.LABOR_MARKET_MIN_WAGE
        if "labor" in market_data and "avg_wage" in market_data["labor"]:
             market_wage = market_data["labor"]["avg_wage"]

        adjustment = -0.2 + (aggressiveness * 0.5)
        offer_wage = market_wage * (1.0 + adjustment)
        offer_wage = max(self.config_module.LABOR_MARKET_MIN_WAGE, offer_wage)

        offer_wage = self._adjust_wage_for_vacancies(firm_state, offer_wage, needed_labor)

        to_hire = needed_labor - current_employees
        if to_hire > 0:
            for _ in range(to_hire):
                 new_orders.append(
                     Order(firm_state.id, "BUY", "labor", 1, offer_wage, "labor")
                 )

        return new_orders

    def _adjust_wage_for_vacancies(self, firm_state: FirmStateDTO, base_offer_wage: float, needed_labor: int) -> float:
        """
        WO-047-B: Competitive Bidding Logic.
        """
        current_employees = firm_state.employee_count
        vacancies = max(0, needed_labor - current_employees)
        
        if vacancies <= 0:
            return base_offer_wage

        total_liabilities = firm_state.total_debt
        if total_liabilities > 0:
            solvency_ratio = firm_state.assets / total_liabilities
            if solvency_ratio < 1.5:
                return base_offer_wage
        
        wage_bill = sum(firm_state.employee_wages.values())
        if wage_bill > 0 and firm_state.assets < wage_bill * 2:
             return base_offer_wage

        increase_rate = min(0.05, 0.01 * vacancies)
        new_wage = base_offer_wage * (1.0 + increase_rate)

        max_affordable = firm_state.assets / (current_employees + vacancies + 1)
        if new_wage > max_affordable:
            new_wage = max(base_offer_wage, max_affordable)

        return max(base_offer_wage, new_wage)
