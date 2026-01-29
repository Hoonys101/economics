from typing import List, Dict
import logging
from simulation.models import Order
from simulation.dtos import DecisionContext, FirmStateDTO, FirmConfigDTO
from simulation.decisions.firm.api import HRPlanDTO

logger = logging.getLogger(__name__)

class HRManager:
    def formulate_plan(self, context: DecisionContext, hiring_aggressiveness: float) -> HRPlanDTO:
        firm = context.state
        config = context.config
        market_data = context.market_data

        orders = self._manage_hiring(firm, hiring_aggressiveness, market_data, config)
        return HRPlanDTO(orders=orders)

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
