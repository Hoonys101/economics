from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Any, Dict
import logging
import random
import math

from simulation.models import Order, StockOrder
from simulation.schemas import FirmActionVector
from simulation.dtos import DecisionContext
from simulation.ai.firm_system2_planner import FirmSystem2Planner
from simulation.markets.stock_market import StockMarket

if TYPE_CHECKING:
    from simulation.firms import Firm

logger = logging.getLogger(__name__)

class CorporateManager:
    """
    CEO Module (WO-027).
    Translates the 6-channel Aggressiveness Vector (Strategy) into concrete Actions (Tactics).
    Owned by AIDrivenFirmDecisionEngine.
    """

    def __init__(self, config_module: Any, logger: Optional[logging.Logger] = None):
        self.config_module = config_module
        self.logger = logger if logger else logging.getLogger(__name__)

    def realize_ceo_actions(
        self,
        firm: Firm,
        context: DecisionContext,
        action_vector: FirmActionVector
    ) -> List[Order]:
        """
        Main entry point. Orchestrates all channel executions.
        """
        orders: List[Order] = []

        # Phase 21: System 2 Strategic Guidance
        # Instantiate planner if not present (Lazy Init)
        if firm.system2_planner is None:
             firm.system2_planner = FirmSystem2Planner(firm, self.config_module)

        guidance = firm.system2_planner.project_future(context.current_time, context.market_data)

        # 0. Procurement Channel (Raw Materials) - WO-030
        procurement_orders = self._manage_procurement(firm, context.market_data, context.markets)
        orders.extend(procurement_orders)

        # Phase 21: Automation Channel (New)
        # Uses Capital Aggressiveness + System 2 Target
        # But wait, Capital Channel is _manage_capex. Automation is different form of capital.
        # Let's add specific method.
        # We can use 'capital_aggressiveness' to split between CAPEX (Machines) and Automation.
        self._manage_automation(firm, action_vector.capital_aggressiveness, guidance, context.current_time, context.government)

        # 1. R&D Channel (Innovation)
        # System 2 guidance might override action vector?
        # Or bias it.
        # For now, let action vector drive execution intensity, but System 2 sets 'strategic priority' or modifies it?
        # Spec: "Personalities dictate the 'Preferred Strategy' ... focus: innovation"
        # The System 2 planner returns 'rd_intensity'.
        # Let's blend them or use System 2 to modify action_vector.
        # But realize_ceo_actions receives a 'fixed' vector from AI.
        # The AI (RL Agent) learns to output the vector.
        # System 2 is 'Cognitive Overhead' or 'Advisor'.
        # If AI is System 1, System 2 should bias the AI? Or bias the execution?
        # Let's bias the execution here.

        rd_agg = action_vector.rd_aggressiveness
        if guidance.get("rd_intensity", 0.0) > 0.1:
             rd_agg = max(rd_agg, 0.5) # Minimum effort if strategic priority

        self._manage_r_and_d(firm, rd_agg, context.current_time)

        # 2. Capital Channel (CAPEX - Physical Machines)
        # If Automation is prioritized, maybe reduce physical capex?
        capex_agg = action_vector.capital_aggressiveness
        self._manage_capex(firm, capex_agg, context.reflux_system, context.current_time)

        # 3. Dividend Channel
        self._manage_dividends(firm, action_vector.dividend_aggressiveness)

        # 4. Debt Channel (Leverage)
        debt_orders = self._manage_debt(firm, action_vector.debt_aggressiveness, context.market_data)
        orders.extend(debt_orders)

        # 5. Pricing Channel (Sales)
        sales_order = self._manage_pricing(firm, action_vector.sales_aggressiveness, context.market_data, context.markets, context.current_time)

        # 6. Hiring Channel (Employment)
        # If automation is high, maybe hire less?
        # _manage_hiring logic calculates needed_labor based on productivity.
        # productivity_factor is TFP.
        # Automation changes Alpha.
        # The 'needed_labor' calculation in _manage_hiring is simplistic: inventory_gap / productivity.
        # It assumes L * TFP = Output.
        # But Cobb-Douglas is Y = TFP * L^a * K^b.
        # We need to update hiring logic to inverse the production function properly!
        hiring_orders = self._manage_hiring(firm, action_vector.hiring_aggressiveness, context.market_data)
        orders.extend(hiring_orders)

        # 7. Secondary Offering (SEO)
        seo_order = self._attempt_secondary_offering(firm, context)
        if seo_order:
            orders.append(seo_order)

        return orders

    def _attempt_secondary_offering(self, firm: Firm, context: DecisionContext) -> Optional[StockOrder]:
        """Sell treasury shares to raise capital when cash is low."""
        startup_cost = getattr(self.config_module, "STARTUP_COST", 30000.0)
        trigger_ratio = getattr(self.config_module, "SEO_TRIGGER_RATIO", 0.5)

        if firm.assets >= startup_cost * trigger_ratio:
            return None
        if firm.treasury_shares <= 0:
            return None

        stock_market = context.markets.get("stock_market")
        if not stock_market or not isinstance(stock_market, StockMarket):
            return None

        max_sell_ratio = getattr(self.config_module, "SEO_MAX_SELL_RATIO", 0.10)
        sell_qty = min(firm.treasury_shares * max_sell_ratio, firm.treasury_shares)

        if sell_qty < 1.0:
            return None

        price = stock_market.get_stock_price(firm.id)
        if price is None or price <= 0:
            price = firm.get_book_value_per_share()

        if price <= 0:
            return None

        order = StockOrder(
            agent_id=firm.id,
            firm_id=firm.id,
            order_type="SELL",
            quantity=sell_qty,
            price=price
        )
        self.logger.info(f"SEO | Firm {firm.id} offering {sell_qty:.1f} shares at {price:.2f}")
        return order

    def _manage_procurement(self, firm: Firm, market_data: Dict[str, Any], markets: Dict[str, Any]) -> List[Order]:
        """
        WO-030: Manage Raw Material Procurement.
        """
        orders = []
        input_config = self.config_module.GOODS.get(firm.specialization, {}).get("inputs", {})

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
                     last_price = self.config_module.GOODS.get(mat, {}).get("initial_price", 10.0)

                bid_price = last_price * 1.05
                orders.append(Order(firm.id, "BUY", mat, deficit, bid_price, mat))

        return orders

    def _manage_automation(self, firm: Firm, aggressiveness: float, guidance: Dict[str, Any], current_time: int, government: Optional[Any] = None) -> None:
        """
        Phase 21: Automation Investment.
        """
        target_a = guidance.get("target_automation", firm.automation_level)
        current_a = firm.automation_level

        if current_a >= target_a:
            return # No investment needed (except maintenance, which is handled implicitly? Or should be explicit?)
            # Firm logic decays automation. So we need to top up.

        gap = target_a - current_a

        # Cost Logic: Base Cost * Asset Scale * Gap
        cost_per_pct = getattr(self.config_module, "AUTOMATION_COST_PER_PCT", 1000.0)
        # Let's treat 'Firm Size' as roughly constant 10000 or Assets.
        # Spec: "Firm Size (Assets)".
        # If Assets are huge, cost is huge.
        # Let's clamp 'Firm Size' factor to avoid runaway costs for rich firms.
        # Or use Log(Assets)?
        # For simplicity and testability: Cost = 1000 * Gap.
        # Wait, if Gap is 0.1 (10%), Cost = 100. Cheap.
        # Spec says: AUTOMATION_COST_PER_PCT = 1000.0 (Base cost scaling).
        # Maybe Cost = 1000 * (Gap * 100)?
        # Let's say to increase 1% (0.01) costs 1000 * scale.
        # Assuming scale = 1.0 for standard firm.
        # Let's just use: Cost = AUTOMATION_COST_PER_PCT * (Gap * 100)
        # So 10% increase = 1000 * 10 = 10,000.

        cost = cost_per_pct * (gap * 100.0)

        # Budget Check (using aggressiveness)
        # If aggressiveness is low, we invest slowly.

        # [Fix] Solvency Check: Reserve buffer for wages (approx 2000.0)
        safety_margin = getattr(self.config_module, "FIRM_SAFETY_MARGIN", 2000.0)
        investable_cash = max(0.0, firm.assets - safety_margin)

        budget = investable_cash * (aggressiveness * 0.5)

        actual_spend = min(cost, budget)

        if actual_spend < 100.0:
            return

        # Execute
        firm.finance.invest_in_automation(actual_spend)

        # WO-044-Track-B: Automation Tax
        # Logic: actual_spend * AUTOMATION_TAX_RATE
        automation_tax_rate = getattr(self.config_module, "AUTOMATION_TAX_RATE", 0.05)
        tax_amount = actual_spend * automation_tax_rate

        if tax_amount > 0 and government:
            if firm.assets >= tax_amount:
                firm.finance.pay_automation_tax(tax_amount, government, current_time)

                self.logger.info(
                    f"AUTOMATION_TAX | Firm {firm.id} paid {tax_amount:.2f} tax on {actual_spend:.2f} investment.",
                    extra={"agent_id": firm.id, "tick": current_time, "tags": ["tax", "automation"]}
                )

        # Calculate gained automation
        # gained = (spend / cost_per_pct) / 100.0
        gained_pct = actual_spend / cost_per_pct
        gained_a = gained_pct / 100.0

        firm.automation_level = min(1.0, firm.automation_level + gained_a)

        self.logger.info(
            f"AUTOMATION | Firm {firm.id} invested {actual_spend:.1f}, level {current_a:.3f} -> {firm.automation_level:.3f}",
            extra={"agent_id": firm.id, "tick": current_time, "tags": ["automation"]}
        )

    def _manage_r_and_d(self, firm: Firm, aggressiveness: float, current_time: int) -> None:
        """
        Innovation Physics.
        """
        if aggressiveness <= 0.1:
            return

        revenue_base = max(firm.revenue_this_turn, firm.assets * 0.05)
        rd_budget_rate = aggressiveness * 0.20
        budget = revenue_base * rd_budget_rate

        # [Fix] Solvency Check
        safety_margin = getattr(self.config_module, "FIRM_SAFETY_MARGIN", 2000.0)
        investable_cash = max(0.0, firm.assets - safety_margin)

        if investable_cash < budget:
            budget = investable_cash * 0.5

        if budget < 10.0:
            return

        firm.finance.invest_in_rd(budget)
        firm.research_history["total_spent"] += budget

        denominator = max(firm.revenue_this_turn * 0.2, 100.0)
        base_chance = min(1.0, budget / denominator)

        avg_skill = 1.0
        if firm.employees:
            avg_skill = sum(getattr(e, 'labor_skill', 1.0) for e in firm.employees) / len(firm.employees)

        success_chance = base_chance * avg_skill

        if random.random() < success_chance:
            firm.research_history["success_count"] += 1
            firm.research_history["last_success_tick"] = current_time
            firm.base_quality += 0.05
            firm.productivity_factor *= 1.05

            self.logger.info(
                f"R&D SUCCESS | Firm {firm.id} spent {budget:.1f}. Quality {firm.base_quality:.2f}, Prod {firm.productivity_factor:.2f}",
                extra={"agent_id": firm.id, "tick": current_time, "tags": ["innovation", "success"]}
            )
        else:
             self.logger.info(
                f"R&D FAIL | Firm {firm.id} spent {budget:.1f}. Chance {success_chance:.1%}",
                extra={"agent_id": firm.id, "tick": current_time, "tags": ["innovation", "fail"]}
            )

    def _manage_capex(self, firm: Firm, aggressiveness: float, reflux_system: Any, current_time: int) -> None:
        """
        Capacity Expansion.
        """
        if aggressiveness <= 0.2:
            return

        # [Fix] Solvency Check
        safety_margin = getattr(self.config_module, "FIRM_SAFETY_MARGIN", 2000.0)
        investable_cash = max(0.0, firm.assets - safety_margin)

        budget = investable_cash * (aggressiveness * 0.5)

        if budget < 100.0:
            return

        firm.finance.invest_in_capex(budget)

        if reflux_system:
             reflux_system.capture(budget, str(firm.id), "capex")

        efficiency = 1.0 / getattr(self.config_module, "CAPITAL_TO_OUTPUT_RATIO", 2.0)
        added_capital = budget * efficiency
        firm.capital_stock += added_capital

        self.logger.info(
            f"CAPEX | Firm {firm.id} invested {budget:.1f}, added {added_capital:.1f} capital.",
            extra={"agent_id": firm.id, "tick": current_time, "tags": ["capex"]}
        )

    def _manage_dividends(self, firm: Firm, aggressiveness: float) -> None:
        """
        Set Dividend Rate.
        """
        base_rate = getattr(self.config_module, "DIVIDEND_RATE_MIN", 0.1)
        max_rate = getattr(self.config_module, "DIVIDEND_RATE_MAX", 0.5)
        firm.dividend_rate = base_rate + (aggressiveness * (max_rate - base_rate))

    def _manage_debt(self, firm: Firm, aggressiveness: float, market_data: Dict) -> List[Order]:
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

    def _manage_pricing(self, firm: Firm, aggressiveness: float, market_data: Dict, markets: Dict, current_time: int) -> Optional[Order]:
        """
        Sales Channel.
        """
        item_id = firm.specialization
        current_inventory = firm.inventory.get(item_id, 0)

        if current_inventory <= 0:
            return None

        market_price = 0.0
        if item_id in market_data:
             market_price = market_data[item_id].get('avg_price', 0)
        if market_price <= 0:
             market_price = firm.last_prices.get(item_id, 0)
        if market_price <= 0:
             market_price = self.config_module.GOODS.get(item_id, {}).get("production_cost", 10.0)

        adjustment = (0.5 - aggressiveness) * 0.4
        target_price = market_price * (1.0 + adjustment)

        sales_vol = getattr(firm, 'last_sales_volume', 1.0)
        if sales_vol <= 0: sales_vol = 1.0
        days_on_hand = current_inventory / sales_vol
        decay = max(0.5, 1.0 - (days_on_hand * 0.005))
        target_price *= decay

        target_price = max(target_price, 0.1)
        firm.last_prices[item_id] = target_price

        qty = min(current_inventory, self.config_module.MAX_SELL_QUANTITY)

        target_market = markets.get(item_id)
        if target_market:
            firm.post_ask(item_id, target_price, qty, target_market, current_time)

        return None

    def _manage_hiring(self, firm: Firm, aggressiveness: float, market_data: Dict) -> List[Order]:
        """
        Hiring Channel.
        Phase 21: Updated to account for Automation in labor demand.
        """
        orders = []
        target_inventory = firm.production_target
        current_inventory = firm.inventory.get(firm.specialization, 0)
        inventory_gap = target_inventory - current_inventory

        if inventory_gap <= 0:
            return []

        # Calculate needed labor with Cobb-Douglas inversion?
        # Y = TFP * L^alpha * K^beta
        # L^alpha = Y / (TFP * K^beta)
        # L = (Y / (TFP * K^beta)) ^ (1/alpha)

        base_alpha = getattr(self.config_module, "LABOR_ALPHA", 0.7)
        automation_reduction = getattr(self.config_module, "AUTOMATION_LABOR_REDUCTION", 0.5)
        alpha_adjusted = base_alpha * (1.0 - (firm.automation_level * automation_reduction))
        beta_adjusted = 1.0 - alpha_adjusted

        capital = max(firm.capital_stock, 1.0)
        tfp = firm.productivity_factor

        # Avoid division by zero
        if tfp <= 0: tfp = 1.0

        needed_labor_calc = 0.0
        try:
             # term = Y / (TFP * K^beta)
             term = inventory_gap / (tfp * (capital ** beta_adjusted))
             needed_labor_calc = term ** (1.0 / alpha_adjusted)
        except Exception:
             needed_labor_calc = 1.0 # Fallback

        # Soft limit removed to allow full employment
        needed_labor = int(needed_labor_calc) + 1

        current_employees = len(firm.employees)

        # A. Firing Logic (Layoffs)
        if current_employees > needed_labor:
            excess = current_employees - needed_labor
            # Don't fire everyone if inventory is just slightly full?
            # Cobb-Douglas needs labor. If we fire all, prod=0.
            # But needed_labor calculated above might be 0 if inventory gap <= 0.
            # If inventory gap <= 0, we have enough stock. We don't need to produce.
            # So firing is rational to save wages.
            # However, firing everyone destroys organization capital.
            # Let's keep at least 1 employee (skeleton crew) if possible, unless bankrupt.

            # Allow firing down to 1
            fire_count = min(excess, max(0, current_employees - 1))

            if fire_count > 0:
                # Fire the most expensive or random? Random for now.
                # Actually we should iterate copy to modify list safely?
                # No, we just call employee.quit().
                # We need to pick employees.
                candidates = firm.employees[:fire_count] # FIFO firing

                # WO-044-Track-C: Strategic Firing Severance Check
                severance_weeks = getattr(self.config_module, "SEVERANCE_PAY_WEEKS", 4)

                for emp in candidates:
                    # Estimate wage (Strategic firing happens before update_needs, so check current wage)
                    wage = firm.employee_wages.get(emp.id, self.config_module.LABOR_MARKET_MIN_WAGE)
                    # Correct for skill
                    skill = getattr(emp, 'labor_skill', 1.0)
                    wage *= skill

                    severance_pay = wage * severance_weeks

                    if firm.assets >= severance_pay:
                        firm.finance.pay_severance(severance_pay)
                        emp.assets += severance_pay

                        emp.quit()
                        self.logger.info(
                            f"LAYOFF | Firm {firm.id} laid off Household {emp.id} with Severance {severance_pay:.2f}. Excess labor.",
                            extra={"tick": 0, "tags": ["hiring", "layoff", "severance"]}
                        )
                    else:
                        self.logger.warning(
                            f"LAYOFF ABORTED | Firm {firm.id} cannot afford Severance {severance_pay:.2f} for Household {emp.id}. Firing cancelled.",
                             extra={"tick": 0, "tags": ["hiring", "layoff_aborted"]}
                        )

                # Firing done. No hiring.
                return []

        # B. Hiring Logic
        market_wage = self.config_module.LABOR_MARKET_MIN_WAGE
        if "labor" in market_data and "avg_wage" in market_data["labor"]:
             market_wage = market_data["labor"]["avg_wage"]

        adjustment = -0.2 + (aggressiveness * 0.5)
        offer_wage = market_wage * (1.0 + adjustment)
        offer_wage = max(self.config_module.LABOR_MARKET_MIN_WAGE, offer_wage)

        # WO-047-B: Competitive Bidding Adjustment
        offer_wage = self._adjust_wage_for_vacancies(firm, offer_wage, needed_labor)

        # Calculate how many to hire
        to_hire = needed_labor - current_employees
        if to_hire > 0:
            for _ in range(to_hire):
                 orders.append(
                     Order(firm.id, "BUY", "labor", 1, offer_wage, "labor")
                 )

        return orders

    def _get_total_liabilities(self, firm: Firm) -> float:
        """Helper to get total liabilities from Bank logic (WO-047-B)."""
        try:
            loan_market = getattr(firm.decision_engine, 'loan_market', None)
            if loan_market and hasattr(loan_market, 'bank') and loan_market.bank:
                debt_summary = loan_market.bank.get_debt_summary(firm.id)
                return debt_summary.get('total_principal', 0.0)
        except Exception:
            pass
        return 0.0

    def _adjust_wage_for_vacancies(self, firm: Firm, base_offer_wage: float, needed_labor: int) -> float:
        """
        WO-047-B: Competitive Bidding Logic.
        If firm has vacancies and is solvent, bid up the wage.
        """
        current_employees = len(firm.employees)
        vacancies = max(0, needed_labor - current_employees)
        
        if vacancies <= 0:
            return base_offer_wage

        # 1. 1.5x Solvency Check (Guardrail)
        total_liabilities = self._get_total_liabilities(firm)
        if total_liabilities > 0:
            solvency_ratio = firm.assets / total_liabilities
            if solvency_ratio < 1.5:
                # Insolvent or risky: Cannot afford bidding war
                return base_offer_wage
        
        # 2. Wage Bill Cap Check (Fallback for 0 liabilities)
        # Check if we have enough cash runway (e.g., 2 ticks)
        # Using current wage bill as proxy
        wage_bill = sum(firm.employee_wages.values()) if firm.employee_wages else 0.0
        if wage_bill > 0 and firm.assets < wage_bill * 2: 
             return base_offer_wage

        # 3. Calculate Increase
        # Increase by 1% per vacancy, max 5%
        increase_rate = min(0.05, 0.01 * vacancies)
        new_wage = base_offer_wage * (1.0 + increase_rate)

        # 4. Absolute Ceiling Check (Safety Net)
        # Ensures firm doesn't commit to a wage causing immediate insolvency next tick
        # Logic: Assets should cover (Current Employees + New Hires + 1) * New Wage
        # This is a bit conservative but safe.
        max_affordable = firm.assets / (current_employees + vacancies + 1)
        if new_wage > max_affordable:
            new_wage = max(base_offer_wage, max_affordable)

        # Ensure we don't accidentally lower it below base
        return max(base_offer_wage, new_wage)
