from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
import logging
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode, MarketContextDTO
from modules.hr.api import IEmployeeDataProvider
from simulation.models import Transaction
from simulation.components.state.firm_state_models import HRState

if TYPE_CHECKING:
    from simulation.dtos.config_dtos import FirmConfigDTO

logger = logging.getLogger(__name__)

from simulation.dtos.hr_dtos import HRPayrollContextDTO

logger = logging.getLogger(__name__)

class HREngine:
    """
    Stateless Engine for HR operations.
    Manages employees, calculates wages (skill + halo), and handles insolvency firing.
    """

    def calculate_wage(self, employee: IEmployeeDataProvider, base_wage: float, config: FirmConfigDTO) -> float:
        """
        Calculates wage based on skill and halo effect.
        """
        # WO-023-B: Skill-based Wage Bonus
        actual_skill = employee.labor_skill

        # WO-Sociologist: Halo Effect (Credential Premium)
        education_level = employee.education_level
        halo_modifier = 1.0 + (education_level * config.halo_effect)

        return base_wage * actual_skill * halo_modifier

    def process_payroll(
        self,
        hr_state: HRState,
        context: HRPayrollContextDTO,
        config: FirmConfigDTO,
    ) -> List[Transaction]:
        """
        Pays wages to employees. Handles insolvency firing if assets are insufficient.
        Returns list of Transactions.
        """
        generated_transactions: List[Transaction] = []
        exchange_rates = context.exchange_rates
        firm_id = context.firm_id
        current_time = context.current_time

        # Calculate survival cost for tax logic
        survival_cost = 10.0 # Default fallback
        if context.tax_policy:
            survival_cost = context.tax_policy.survival_cost

        # Iterate over copy to allow modification of hr_state.employees
        for employee in list(hr_state.employees):
            # Validate employee
            if employee.employer_id != firm_id or not employee.is_employed:
                self.remove_employee(hr_state, employee)
                continue

            base_wage = hr_state.employee_wages.get(employee.id, context.labor_market_min_wage)
            wage = self.calculate_wage(employee, base_wage, config)

            # Affordability Check (Operational Awareness: Total Liquid Assets)
            total_liquid_assets = 0.0

            # Helper for conversion
            def convert(amt, cur):
                if cur == DEFAULT_CURRENCY: return amt
                rate = exchange_rates.get(cur, 0.0)
                return amt * rate

            for cur, amount in context.wallet_balances.items():
                total_liquid_assets += convert(amount, cur)

            current_balance = context.wallet_balances.get(DEFAULT_CURRENCY, 0.0)

            if current_balance >= wage:
                # Calculate Tax
                income_tax = 0.0
                if context.tax_policy:
                    # Calculation logic: previously government.calculate_income_tax
                    # For now, we assume the DTO provides the rate or we implement a standard logic
                    # If the government logic is complex, we should have a standalone TaxEngine.
                    # For this refactor, we apply a simple rate provided in the policy.
                    income_tax = wage * context.tax_policy.income_tax_rate if wage > survival_cost else 0.0

                net_wage = wage - income_tax

                # Transaction 1: Net Wage (Firm -> Employee)
                tx_wage = Transaction(
                    buyer_id=firm_id, # Payer
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
                if income_tax > 0 and context.tax_policy:
                    tx_tax = Transaction(
                        buyer_id=firm_id, # Payer
                        seller_id=context.tax_policy.government_agent_id, # Payee
                        item_id="income_tax",
                        quantity=1.0,
                        price=income_tax,
                        market_id="system",
                        transaction_type="tax",
                        time=current_time
                    )
                    generated_transactions.append(tx_tax)

                # Track Labor Income (Side Effect on Employee)
                # Note: This is an Abstraction Leak (direct mutation of agent).
                # Future Task: Return this in a DTO for the Orchestrator to apply.
                employee.labor_income_this_tick = (employee.labor_income_this_tick or 0.0) + net_wage

            elif total_liquid_assets >= wage:
                # Solvent but Illiquid -> Zombie
                self._record_zombie_wage(hr_state, firm_id, employee, wage, current_time, current_balance, config)
            else:
                # Insolvent -> Fire
                # This also needs handle-less refactoring, but for now we pass the balance
                self._handle_insolvency_transactions(hr_state, firm_id, config, employee, wage, current_time, generated_transactions, current_balance)

        return generated_transactions

    def _record_zombie_wage(self, hr_state: HRState, firm_id: int, employee: IEmployeeDataProvider, wage: float, current_time: int, current_balance: float, config: FirmConfigDTO) -> None:
        """Records an unpaid wage without firing the employee."""
        if employee.id not in hr_state.unpaid_wages:
            hr_state.unpaid_wages[employee.id] = []

        hr_state.unpaid_wages[employee.id].append((current_time, wage))

        # Prune old unpaid wages
        ticks_per_year = getattr(config, "ticks_per_year", 365)
        cutoff_tick = current_time - (ticks_per_year // 4)

        hr_state.unpaid_wages[employee.id] = [
            (t, w) for t, w in hr_state.unpaid_wages[employee.id]
            if t >= cutoff_tick
        ]

        logger.warning(
            f"ZOMBIE | Firm {firm_id} cannot afford wage for Household {employee.id}. Recorded as unpaid wage.",
            extra={"tick": current_time, "agent_id": firm_id, "wage_deficit": wage - current_balance, "total_unpaid": len(hr_state.unpaid_wages[employee.id])}
        )

    def _handle_insolvency_transactions(self, hr_state: HRState, firm_id: int, config: FirmConfigDTO, employee: IEmployeeDataProvider, wage: float, current_time: int, tx_list: List[Transaction], current_balance: float):
        """
        Handles case where firm cannot afford wage.
        Attempts severance pay; if fails, zombie state.
        """
        severance_weeks = config.severance_pay_weeks
        severance_pay = wage * severance_weeks

        if current_balance >= severance_pay:
            # Fire with severance
            tx = Transaction(
                buyer_id=firm_id,
                seller_id=employee.id,
                item_id="severance_pay",
                quantity=1.0,
                price=severance_pay,
                market_id="labor",
                transaction_type="severance",
                time=current_time
            )
            tx_list.append(tx)

            logger.info(
                f"SEVERANCE | Firm {firm_id} paid severance {severance_pay:.2f} to Household {employee.id}. Firing due to insolvency.",
                extra={"tick": current_time, "agent_id": firm_id, "severance_pay": severance_pay}
            )

            employee.quit()
            self.remove_employee(hr_state, employee)
        else:
            # Fallback to Zombie
            self._record_zombie_wage(hr_state, firm_id, employee, wage, current_time, current_balance, config)

    def hire(self, hr_state: HRState, employee: IEmployeeDataProvider, wage: float, current_tick: int = 0):
        hr_state.employees.append(employee)
        hr_state.employee_wages[employee.id] = wage
        hr_state.hires_last_tick += 1
        employee.employment_start_tick = current_tick

    def remove_employee(self, hr_state: HRState, employee: IEmployeeDataProvider):
        if employee in hr_state.employees:
            hr_state.employees.remove(employee)
        if employee.id in hr_state.employee_wages:
            del hr_state.employee_wages[employee.id]

    def create_fire_transaction(self, hr_state: HRState, firm_id: int, wallet_balance: float, employee_id: int, severance_pay: float, current_time: int) -> Optional[Transaction]:
        """
        Creates a severance transaction to fire an employee.
        Does NOT execute transfer or remove employee.
        """
        employee = next((e for e in hr_state.employees if e.id == employee_id), None)
        if not employee:
            return None

        # Check funds directly on wallet balance
        if wallet_balance < severance_pay:
             logger.warning(f"INTERNAL_EXEC | Firm {firm_id} cannot afford severance to fire {employee_id}.")
             return None

        return Transaction(
            buyer_id=firm_id,
            seller_id=employee.id,
            item_id="Severance",
            quantity=1.0,
            price=severance_pay,
            market_id="system", # or labor?
            transaction_type="severance",
            time=current_time,
            currency=DEFAULT_CURRENCY
        )

    def finalize_firing(self, hr_state: HRState, employee_id: int):
        """
        Removes employee from state and triggers quit().
        Should be called after successful severance payment.
        """
        employee = next((e for e in hr_state.employees if e.id == employee_id), None)
        if employee:
             employee.quit()
             self.remove_employee(hr_state, employee)
