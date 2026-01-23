from __future__ import annotations
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.firms import Firm

logger = logging.getLogger(__name__)

class HRDepartment:
    """
    Manages employees, calculates wages (skill + halo), and handles insolvency firing.
    Extracted from Firm class (SoC Refactor).
    """
    def __init__(self, firm: Firm):
        self.firm = firm
        self.employees: List[Household] = []
        self.employee_wages: Dict[int, float] = {}  # AgentID -> Wage
        self.hires_last_tick: int = 0

    def calculate_wage(self, employee: Household, base_wage: float) -> float:
        """
        Calculates wage based on skill and halo effect.
        """
        # WO-023-B: Skill-based Wage Bonus
        actual_skill = getattr(employee, 'labor_skill', 1.0)

        # WO-Sociologist: Halo Effect (Credential Premium)
        education_level = getattr(employee, 'education_level', 0)
        halo_modifier = 1.0 + (education_level * getattr(self.firm.config_module, "HALO_EFFECT", 0.0))

        return base_wage * actual_skill * halo_modifier

    def process_payroll(self, current_time: int, government: Optional[Any], market_data: Optional[Dict[str, Any]], settlement_system: Any = None) -> float:
        """
        Pays wages to employees. Handles insolvency firing if assets are insufficient.
        Returns total wages paid.
        """
        total_wages = 0.0
        total_tax_withheld = 0.0

        # Calculate survival cost for tax logic
        survival_cost = 10.0 # Default fallback
        if government and market_data:
            survival_cost = government.get_survival_cost(market_data)

        # Iterate over copy to allow modification
        for employee in list(self.employees):
            # Defensive checks
            if not hasattr(employee, 'employer_id') or not hasattr(employee, 'is_employed'):
                self.employees.remove(employee)
                continue

            if employee.employer_id != self.firm.id or not employee.is_employed:
                self.employees.remove(employee)
                if employee.id in self.employee_wages:
                    del self.employee_wages[employee.id]
                continue

            base_wage = self.employee_wages.get(employee.id, self.firm.config_module.LABOR_MARKET_MIN_WAGE)
            wage = self.calculate_wage(employee, base_wage)

            # Affordability Check
            if self.firm.assets >= wage:
                # Calculate Tax
                income_tax = 0.0
                if government:
                    income_tax = government.calculate_income_tax(wage, survival_cost)

                net_wage = wage - income_tax

                # Atomic Transfer 1: Net Wage -> Employee
                if settlement_system:
                    settlement_system.transfer(self.firm, employee, net_wage, "wage_net")
                else:
                    self.firm._sub_assets(net_wage)
                    employee._add_assets(net_wage)

                # Track Labor Income
                if hasattr(employee, "labor_income_this_tick"):
                    employee.labor_income_this_tick += net_wage

                # Atomic Transfer 2: Tax -> Government (Withholding)
                if income_tax > 0 and government:
                    # government.collect_tax handles settlement if configured
                    # We pass self.firm as payer (Withholding Agent)
                    government.collect_tax(income_tax, "income_tax", self.firm, current_time)
                    total_tax_withheld += income_tax

                total_wages += wage
            else:
                # Insolvency Handling
                self._handle_insolvency(employee, wage, settlement_system)

        return total_wages

    def _handle_insolvency(self, employee: Household, wage: float, settlement_system: Any = None):
        """
        Handles case where firm cannot afford wage.
        Attempts severance pay; if fails, zombie state (unpaid retention).
        """
        severance_weeks = getattr(self.firm.config_module, "SEVERANCE_PAY_WEEKS", 4)
        severance_pay = wage * severance_weeks

        # Delegate to FinanceDepartment which now handles settlement
        if self.firm.finance.pay_severance(employee, severance_pay, settlement_system):
            self.firm.logger.info(
                f"SEVERANCE | Firm {self.firm.id} paid severance {severance_pay:.2f} to Household {employee.id}. Firing due to insolvency.",
                extra={"tick": self.firm.decision_engine.context.current_time if hasattr(self.firm.decision_engine, 'context') else 0, "agent_id": self.firm.id, "severance_pay": severance_pay}
            )

            employee.quit()
            self.remove_employee(employee)
        else:
            # Zombie Employee
            self.firm.logger.warning(
                f"ZOMBIE | Firm {self.firm.id} cannot afford wage OR severance for Household {employee.id}. Employment retained (unpaid).",
                extra={"tick": 0, "agent_id": self.firm.id, "wage_deficit": wage - self.firm.assets}
            )

    def hire(self, employee: Household, wage: float):
        self.employees.append(employee)
        self.employee_wages[employee.id] = wage
        self.hires_last_tick += 1

    def remove_employee(self, employee: Household):
        if employee in self.employees:
            self.employees.remove(employee)
        if employee.id in self.employee_wages:
            del self.employee_wages[employee.id]

    def get_total_labor_skill(self) -> float:
        return sum(getattr(emp, 'labor_skill', 1.0) for emp in self.employees)

    def get_avg_skill(self) -> float:
        if not self.employees:
            return 0.0
        return self.get_total_labor_skill() / len(self.employees)
