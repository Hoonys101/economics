from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
import logging
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode, MarketContextDTO
from modules.hr.api import IEmployeeDataProvider
from simulation.models import Transaction
from simulation.components.state.firm_state_models import HRState
from simulation.dtos.hr_dtos import HRPayrollContextDTO, HRPayrollResultDTO, EmployeeUpdateDTO

if TYPE_CHECKING:
    from modules.simulation.dtos.api import FirmConfigDTO

logger = logging.getLogger(__name__)

class HREngine:
    """
    Stateless Engine for HR operations.
    Manages employees, calculates wages (skill + halo), and handles insolvency firing.
    """

    def calculate_wage(self, employee: IEmployeeDataProvider, base_wage: int, config: FirmConfigDTO) -> int:
        """
        Calculates wage based on skill and halo effect. Returns int pennies.
        """
        # WO-023-B: Skill-based Wage Bonus
        actual_skill = employee.labor_skill

        # WO-Sociologist: Halo Effect (Credential Premium)
        education_level = employee.education_level
        halo_modifier = 1.0 + (education_level * config.halo_effect)

        return int(base_wage * actual_skill * halo_modifier)

    def process_payroll(
        self,
        hr_state: HRState,
        context: HRPayrollContextDTO,
        config: FirmConfigDTO,
    ) -> HRPayrollResultDTO:
        """
        Processes payroll and returns a DTO with transactions and employee updates.
        This method MUST NOT have external side-effects.
        """
        transactions: List[Transaction] = []
        employee_updates: List[EmployeeUpdateDTO] = []

        exchange_rates = context.exchange_rates
        firm_id = context.firm_id
        current_time = context.current_time

        # Calculate survival cost for tax logic
        survival_cost = 1000 # Default fallback (10.00)
        if context.tax_policy:
            survival_cost = context.tax_policy.survival_cost

        # Create a local copy of wallet balances to simulate spending without mutating the input DTO
        simulated_balances = context.wallet_balances.copy()

        # Iterate over copy to allow modification of hr_state.employees (if we were removing them,
        # though now we defer removal for firing cases)
        # Note: Validation removal still happens immediately as it's state cleanup.
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

            for cur, amount in simulated_balances.items():
                total_liquid_assets += convert(amount, cur)

            current_balance = simulated_balances.get(DEFAULT_CURRENCY, 0)

            if current_balance >= wage:
                # Calculate Tax
                income_tax = 0
                if context.tax_policy:
                    # Cast to int for pennies
                    income_tax = int(wage * context.tax_policy.income_tax_rate) if wage > survival_cost else 0

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
                transactions.append(tx_wage)

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
                    transactions.append(tx_tax)

                # Schedule Employee Update (Income)
                employee_updates.append(
                    EmployeeUpdateDTO(employee_id=employee.id, net_income=net_wage)
                )

                # Decrement virtual balance for next iteration check (local simulation of balance)
                simulated_balances[DEFAULT_CURRENCY] = current_balance - wage # Simplify: assume all in default currency

            elif total_liquid_assets >= wage:
                # Solvent but Illiquid -> Zombie
                self._record_zombie_wage(hr_state, firm_id, employee, wage, current_time, current_balance, config)
            else:
                # Insolvent -> Fire
                self._handle_insolvency_transactions(
                    hr_state, firm_id, config, employee, wage, current_time,
                    transactions, employee_updates, current_balance
                )

        return HRPayrollResultDTO(transactions=transactions, employee_updates=employee_updates)

    def _record_zombie_wage(self, hr_state: HRState, firm_id: int, employee: IEmployeeDataProvider, wage: int, current_time: int, current_balance: int, config: FirmConfigDTO) -> None:
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

    def _handle_insolvency_transactions(
        self,
        hr_state: HRState,
        firm_id: int,
        config: FirmConfigDTO,
        employee: IEmployeeDataProvider,
        wage: int,
        current_time: int,
        tx_list: List[Transaction],
        updates_list: List[EmployeeUpdateDTO],
        current_balance: int
    ):
        """
        Handles case where firm cannot afford wage.
        Attempts severance pay; if fails, zombie state.
        """
        severance_weeks = config.severance_pay_weeks
        severance_pay = int(wage * severance_weeks)

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
                f"SEVERANCE | Firm {firm_id} paying severance {severance_pay} to Household {employee.id}. Scheduled for firing.",
                extra={"tick": current_time, "agent_id": firm_id, "severance_pay": severance_pay}
            )

            # Schedule Firing
            updates_list.append(
                EmployeeUpdateDTO(employee_id=employee.id, fire_employee=True, severance_pay=severance_pay)
            )
        else:
            # Fallback to Zombie
            self._record_zombie_wage(hr_state, firm_id, employee, wage, current_time, current_balance, config)

    def hire(self, hr_state: HRState, employee: IEmployeeDataProvider, wage: int, current_tick: int = 0):
        hr_state.employees.append(employee)
        hr_state.employee_wages[employee.id] = wage
        hr_state.hires_last_tick += 1
        employee.employment_start_tick = current_tick

    def remove_employee(self, hr_state: HRState, employee: IEmployeeDataProvider):
        if employee in hr_state.employees:
            hr_state.employees.remove(employee)
        if employee.id in hr_state.employee_wages:
            del hr_state.employee_wages[employee.id]

    def create_fire_transaction(self, hr_state: HRState, firm_id: int, wallet_balance: int, employee_id: int, severance_pay: int, current_time: int) -> Optional[Transaction]:
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
        Removes employee from state.
        Should be called after successful severance payment and employee.quit().
        """
        employee = next((e for e in hr_state.employees if e.id == employee_id), None)
        if employee:
             # employee.quit() is now handled by the Orchestrator
             self.remove_employee(hr_state, employee)
