from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
import logging
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode, MarketContextDTO

if TYPE_CHECKING:
    from simulation.core_agents import Household
    from simulation.firms import Firm
    from simulation.models import Transaction

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
        self.unpaid_wages: Dict[int, List[Tuple[int, float]]] = {} # AgentID -> List[(tick, amount)]
        self.hires_last_tick: int = 0

    def calculate_wage(self, employee: Household, base_wage: float) -> float:
        """
        Calculates wage based on skill and halo effect.
        """
        # WO-023-B: Skill-based Wage Bonus
        actual_skill = getattr(employee, 'labor_skill', 1.0)

        # WO-Sociologist: Halo Effect (Credential Premium)
        education_level = getattr(employee, 'education_level', 0)
        halo_modifier = 1.0 + (education_level * self.firm.config.halo_effect)

        return base_wage * actual_skill * halo_modifier

    def process_payroll(self, current_time: int, government: Optional[Any], market_data: Optional[Dict[str, Any]], market_context: MarketContextDTO) -> List[Transaction]:
        """
        Pays wages to employees. Handles insolvency firing if assets are insufficient.
        Returns list of Transactions.
        Refactored for Multi-Currency Operational Awareness (TD-032).
        """
        from simulation.models import Transaction

        generated_transactions: List[Transaction] = []
        exchange_rates = market_context['exchange_rates']

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

            base_wage = self.employee_wages.get(employee.id, self.firm.config.labor_market_min_wage)
            wage = self.calculate_wage(employee, base_wage)

            # Affordability Check (Operational Awareness: Total Liquid Assets)
            # TD-032: Check total liquid assets converted to primary to prevent firing if solvent in other currencies.
            total_liquid_assets = 0.0
            for cur, amount in self.firm.finance.balance.items():
                total_liquid_assets += self.firm.finance.convert_to_primary(amount, cur, exchange_rates)

            # Check if we can pay specifically in the wage currency (assumed DEFAULT_CURRENCY for now)
            current_balance = self.firm.finance.balance.get(DEFAULT_CURRENCY, 0.0)

            if current_balance >= wage:
                # Calculate Tax
                income_tax = 0.0
                if government:
                    income_tax = government.calculate_income_tax(wage, survival_cost)

                net_wage = wage - income_tax

                # Transaction 1: Net Wage (Firm -> Employee)
                tx_wage = Transaction(
                    buyer_id=self.firm.id, # Payer
                    seller_id=employee.id, # Payee
                    item_id="labor_wage",
                    quantity=1.0,
                    price=net_wage,
                    market_id="labor",
                    transaction_type="wage",
                    time=current_time
                )
                generated_transactions.append(tx_wage)

                # Transaction 2: Income Tax (Firm -> Government) [Withholding]
                if income_tax > 0 and government:
                    tx_tax = Transaction(
                        buyer_id=self.firm.id, # Payer
                        seller_id=government.id, # Payee
                        item_id="income_tax",
                        quantity=1.0,
                        price=income_tax,
                        market_id="system",
                        transaction_type="tax",
                        time=current_time
                    )
                    generated_transactions.append(tx_tax)

                # Track Labor Income (Side Effect)
                if hasattr(employee, "labor_income_this_tick"):
                    employee.labor_income_this_tick += net_wage

            elif total_liquid_assets >= wage:
                # TD-032: Solvent but Illiquid in Wage Currency -> Zombie (Unpaid Wage) without Firing
                self._record_zombie_wage(employee, wage, current_time)
            else:
                # Insolvent -> Fire (via insolvency handler)
                self._handle_insolvency_transactions(employee, wage, current_time, generated_transactions)

        return generated_transactions

    def _record_zombie_wage(self, employee: Household, wage: float, current_time: int) -> None:
        """Records an unpaid wage without firing the employee."""
        # Record unpaid wage for Tier 1 claim in liquidation
        if employee.id not in self.unpaid_wages:
            self.unpaid_wages[employee.id] = []

        self.unpaid_wages[employee.id].append((current_time, wage))

        # Prune old unpaid wages (older than 3 months)
        ticks_per_year = getattr(self.firm.config, "ticks_per_year", 365)
        # 3 months = 1/4 year
        cutoff_tick = current_time - (ticks_per_year // 4)

        self.unpaid_wages[employee.id] = [
            (t, w) for t, w in self.unpaid_wages[employee.id]
            if t >= cutoff_tick
        ]

        # Use balance.get for logging deficit
        current_balance = self.firm.finance.balance.get(DEFAULT_CURRENCY, 0.0)
        self.firm.logger.warning(
            f"ZOMBIE | Firm {self.firm.id} cannot afford wage for Household {employee.id}. Recorded as unpaid wage.",
            extra={"tick": current_time, "agent_id": self.firm.id, "wage_deficit": wage - current_balance, "total_unpaid": len(self.unpaid_wages[employee.id])}
        )

    def _handle_insolvency_transactions(self, employee: Household, wage: float, current_time: int, tx_list: List[Transaction]):
        """
        Handles case where firm cannot afford wage.
        Attempts severance pay; if fails, zombie state (unpaid retention).
        """
        from simulation.models import Transaction

        severance_weeks = self.firm.config.severance_pay_weeks
        severance_pay = wage * severance_weeks

        # Refactor: Use finance.balance
        current_balance = self.firm.finance.balance.get(DEFAULT_CURRENCY, 0.0)
        if current_balance >= severance_pay:
            # Fire with severance (Transaction)
            tx = Transaction(
                buyer_id=self.firm.id,
                seller_id=employee.id,
                item_id="severance_pay",
                quantity=1.0,
                price=severance_pay,
                market_id="labor",
                transaction_type="severance",
                time=current_time
            )
            tx_list.append(tx)

            self.firm.logger.info(
                f"SEVERANCE | Firm {self.firm.id} paid severance {severance_pay:.2f} to Household {employee.id}. Firing due to insolvency.",
                extra={"tick": current_time, "agent_id": self.firm.id, "severance_pay": severance_pay}
            )

            employee.quit()
            self.remove_employee(employee)
        else:
            # Fallback to Zombie if we can't even afford severance
            self._record_zombie_wage(employee, wage, current_time)

    def hire(self, employee: Household, wage: float, current_tick: int = 0):
        self.employees.append(employee)
        self.employee_wages[employee.id] = wage
        self.hires_last_tick += 1

        # Set employment start tick for tenure calculation (Tier 1 Severance)
        if hasattr(employee, '_econ_state'):
            employee._econ_state.employment_start_tick = current_tick

    def remove_employee(self, employee: Household):
        if employee in self.employees:
            self.employees.remove(employee)
        if employee.id in self.employee_wages:
            del self.employee_wages[employee.id]

    def fire_employee(self, employee_id: int, severance_pay: float) -> bool:
        """
        Fires an employee with severance pay.
        Returns True if successful (found and paid), False otherwise.
        """
        employee = next((e for e in self.employees if e.id == employee_id), None)
        if employee:
            if self.firm.finance.pay_severance(employee, severance_pay):
                employee.quit()
                self.remove_employee(employee)
                self.firm.logger.info(f"INTERNAL_EXEC | Firm {self.firm.id} fired employee {employee_id}.")
                return True
            else:
                self.firm.logger.warning(f"INTERNAL_EXEC | Firm {self.firm.id} failed to fire {employee_id} (insufficient funds).")
        return False

    def get_total_labor_skill(self) -> float:
        return sum(getattr(emp, 'labor_skill', 1.0) for emp in self.employees)

    def get_avg_skill(self) -> float:
        if not self.employees:
            return 0.0
        return self.get_total_labor_skill() / len(self.employees)
