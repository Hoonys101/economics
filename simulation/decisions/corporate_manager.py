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
        self._manage_automation(firm, action_vector.capital_aggressiveness, guidance, context.current_time, context.government)

        # 1. R&D Channel (Innovation)
        rd_agg = action_vector.rd_aggressiveness
        if guidance.get("rd_intensity", 0.0) > 0.1:
             rd_agg = max(rd_agg, 0.5) # Minimum effort if strategic priority

        self._manage_r_and_d(firm, rd_agg, context.current_time)

        # 2. Capital Channel (CAPEX - Physical Machines)
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

        # Use encapsulated cash access
        if firm.finance.cash >= startup_cost * trigger_ratio:
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
            # Use FinanceDepartment method directly
            price = firm.finance.get_book_value_per_share()

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
            return

        gap = target_a - current_a
        cost_per_pct = getattr(self.config_module, "AUTOMATION_COST_PER_PCT", 1000.0)
        cost = cost_per_pct * (gap * 100.0)

        safety_margin = getattr(self.config_module, "FIRM_SAFETY_MARGIN", 2000.0)
        # Use encapsulated cash access
        investable_cash = max(0.0, firm.finance.cash - safety_margin)

        budget = investable_cash * (aggressiveness * 0.5)

        actual_spend = min(cost, budget)

        if actual_spend < 100.0:
            return

        # Execute using Finance Encapsulation
        if firm.finance.invest_in_automation(actual_spend):
            # WO-044-Track-B: Automation Tax
            automation_tax_rate = getattr(self.config_module, "AUTOMATION_TAX_RATE", 0.05)
            tax_amount = actual_spend * automation_tax_rate

            if tax_amount > 0 and government:
                # Use encapsulated tax payment
                # If pay_adhoc_tax returns False (insufficient funds), we log or ignore?
                # The original logic was: check funds, deduct if sufficient.
                # pay_adhoc_tax handles this check.
                if firm.finance.pay_adhoc_tax(tax_amount, "automation_tax", government, current_time):
                    self.logger.info(
                        f"AUTOMATION_TAX | Firm {firm.id} paid {tax_amount:.2f} tax on {actual_spend:.2f} investment.",
                        extra={"agent_id": firm.id, "tick": current_time, "tags": ["tax", "automation"]}
                    )

            # Calculate gained automation
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

        # Use direct component access for revenue and cash
        revenue_base = max(firm.finance.revenue_this_turn, firm.finance.cash * 0.05)
        rd_budget_rate = aggressiveness * 0.20
        budget = revenue_base * rd_budget_rate

        safety_margin = getattr(self.config_module, "FIRM_SAFETY_MARGIN", 2000.0)
        investable_cash = max(0.0, firm.finance.cash - safety_margin)

        if investable_cash < budget:
            budget = investable_cash * 0.5

        if budget < 10.0:
            return

        # Use Finance Encapsulation
        if firm.finance.invest_in_rd(budget):
            firm.research_history["total_spent"] += budget

            denominator = max(firm.finance.revenue_this_turn * 0.2, 100.0)
            base_chance = min(1.0, budget / denominator)

            avg_skill = 1.0
            # Use direct component access for employees
            employees = firm.hr.employees
            if employees:
                avg_skill = sum(getattr(e, 'labor_skill', 1.0) for e in employees) / len(employees)

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

        safety_margin = getattr(self.config_module, "FIRM_SAFETY_MARGIN", 2000.0)
        investable_cash = max(0.0, firm.finance.cash - safety_margin)

        budget = investable_cash * (aggressiveness * 0.5)

        if budget < 100.0:
            return

        # Use Finance Encapsulation
        if firm.finance.invest_in_capex(budget):
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
        rate = base_rate + (aggressiveness * (max_rate - base_rate))

        # Use Finance Encapsulation
        firm.finance.set_dividend_rate(rate)

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

        # Use encapsulated cash access
        current_assets = max(firm.finance.cash, 1.0)
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
            # Use encapsulated cash access
            repay_amount = min(excess_debt, firm.finance.cash * 0.5)

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

        # Use direct component access
        sales_vol = getattr(firm.finance, 'last_sales_volume', 1.0)
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

        base_alpha = getattr(self.config_module, "LABOR_ALPHA", 0.7)
        automation_reduction = getattr(self.config_module, "AUTOMATION_LABOR_REDUCTION", 0.5)
        alpha_adjusted = base_alpha * (1.0 - (firm.automation_level * automation_reduction))
        beta_adjusted = 1.0 - alpha_adjusted

        capital = max(firm.capital_stock, 1.0)
        tfp = firm.productivity_factor

        if tfp <= 0: tfp = 1.0

        needed_labor_calc = 0.0
        try:
             term = inventory_gap / (tfp * (capital ** beta_adjusted))
             needed_labor_calc = term ** (1.0 / alpha_adjusted)
        except Exception:
             needed_labor_calc = 1.0

        needed_labor = int(needed_labor_calc) + 1

        # Use direct component access
        current_employees = len(firm.hr.employees)

        # A. Firing Logic (Layoffs)
        if current_employees > needed_labor:
            excess = current_employees - needed_labor
            fire_count = min(excess, max(0, current_employees - 1))

            if fire_count > 0:
                # Use direct component access
                candidates = firm.hr.employees[:fire_count]

                severance_weeks = getattr(self.config_module, "SEVERANCE_PAY_WEEKS", 4)

                for emp in candidates:
                    # Use direct component access
                    wage = firm.hr.employee_wages.get(emp.id, self.config_module.LABOR_MARKET_MIN_WAGE)
                    skill = getattr(emp, 'labor_skill', 1.0)
                    wage *= skill

                    severance_pay = wage * severance_weeks

                    if firm.finance.pay_severance(emp, severance_pay):
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

                return []

        # B. Hiring Logic
        market_wage = self.config_module.LABOR_MARKET_MIN_WAGE
        if "labor" in market_data and "avg_wage" in market_data["labor"]:
             market_wage = market_data["labor"]["avg_wage"]

        adjustment = -0.2 + (aggressiveness * 0.5)
        offer_wage = market_wage * (1.0 + adjustment)
        offer_wage = max(self.config_module.LABOR_MARKET_MIN_WAGE, offer_wage)

        offer_wage = self._adjust_wage_for_vacancies(firm, offer_wage, needed_labor)

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
        # Use direct component access
        current_employees = len(firm.hr.employees)
        vacancies = max(0, needed_labor - current_employees)
        
        if vacancies <= 0:
            return base_offer_wage

        total_liabilities = self._get_total_liabilities(firm)
        if total_liabilities > 0:
            # Use encapsulated cash access
            solvency_ratio = firm.finance.cash / total_liabilities
            if solvency_ratio < 1.5:
                return base_offer_wage
        
        # Use direct component access
        wage_bill = sum(firm.hr.employee_wages.values()) if firm.hr.employee_wages else 0.0
        # Use encapsulated cash access
        if wage_bill > 0 and firm.finance.cash < wage_bill * 2:
             return base_offer_wage

        increase_rate = min(0.05, 0.01 * vacancies)
        new_wage = base_offer_wage * (1.0 + increase_rate)

        # Use encapsulated cash access
        max_affordable = firm.finance.cash / (current_employees + vacancies + 1)
        if new_wage > max_affordable:
            new_wage = max(base_offer_wage, max_affordable)

        return max(base_offer_wage, new_wage)
