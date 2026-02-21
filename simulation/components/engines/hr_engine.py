from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
import logging
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode, MarketContextDTO
from modules.hr.api import IEmployeeDataProvider
from simulation.models import Transaction, Order
from simulation.components.state.firm_state_models import HRState
from simulation.dtos.hr_dtos import HRPayrollContextDTO, HRPayrollResultDTO, EmployeeUpdateDTO
from modules.firm.api import HRDecisionInputDTO, HRDecisionOutputDTO, IHREngine

if TYPE_CHECKING:
    from modules.simulation.dtos.api import FirmConfigDTO, FirmStateDTO

logger = logging.getLogger(__name__)

class HREngine(IHREngine):
    """
    Stateless Engine for HR operations.
    Manages employees, calculates wages (skill + halo), and handles insolvency firing.
    """

    def manage_workforce(self, input_dto: HRDecisionInputDTO) -> HRDecisionOutputDTO:
        """
        Decides on hiring and firing based on production needs and budget constraints.
        Ported from RuleBasedFirmDecisionEngine.
        """
        orders: List[Order] = []
        firing_ids: List[int] = []
        wage_updates: Dict[int, int] = {}

        firm_state = input_dto.firm_snapshot
        config = input_dto.config
        current_tick = input_dto.current_tick
        budget_plan = input_dto.budget_plan

        # 1. Calculate Needed Labor
        # Logic from RuleBasedFirmDecisionEngine._calculate_needed_labor
        item_id = firm_state.production.specialization
        target_quantity = firm_state.production.production_target
        current_inventory = firm_state.production.inventory.get(item_id, 0)

        needed_production = max(0, target_quantity - current_inventory)
        productivity_factor = firm_state.production.productivity_factor

        if productivity_factor <= 0:
            needed_labor = 999999.0
        else:
            needed_labor = needed_production / productivity_factor

        target_headcount = int(needed_labor)

        # 2. Compare with current headcount
        current_employees_list = firm_state.hr.employees # Note: FirmSnapshotDTO has list of IDs? No, HRStateDTO has IDs.
        # Wait, FirmSnapshotDTO.hr is HRStateDTO.
        # HRStateDTO has `employees: List[int]` (IDs) and `employees_data: Dict[int, Dict]`.
        # So I can get count.
        current_headcount = len(firm_state.hr.employees)

        # 3. Calculate Wages & Scale (NEW)

        # Calculate Target Wage (used for both Hiring and Scaling)
        base_wage = input_dto.labor_market_avg_wage # Pennies
        sensitivity = 0.1
        max_premium = 2.0

        profit_history = firm_state.finance.profit_history
        avg_profit = sum(profit_history) / len(profit_history) if profit_history else 0.0

        profit_based_premium = avg_profit / (base_wage * 10.0) if base_wage > 0 else 0.0
        wage_premium = max(0, min(profit_based_premium * sensitivity, max_premium))

        target_wage = int(base_wage * (1 + wage_premium))

        # Wage Scaling: Update existing employees if underpaid
        for emp_id, emp_data in firm_state.hr.employees_data.items():
            current_wage = emp_data.get('wage', 0)
            if current_wage < target_wage:
                wage_updates[emp_id] = target_wage

        # Budget Constraint: Check if we can afford current + new employees
        # Use updated wages for current employees in calculation
        current_wage_bill = 0
        for emp_id, emp_data in firm_state.hr.employees_data.items():
             w = wage_updates.get(emp_id, emp_data.get('wage', 0))
             current_wage_bill += w

        # 4. Hire or Fire

        # Check Firing
        # Logic from RuleBasedFirmDecisionEngine._fire_excess_labor
        # "if current_employees > needed_labor + 1"
        if current_headcount > target_headcount + 1:
            excess = current_headcount - target_headcount
            excess = min(excess, max(0, current_headcount - 1)) # Don't fire everyone? (implied by max(0, current-1))

            if excess > 0:
                # Find candidates (lowest skill? random? last hired?)
                # Current logic was just firm.hr.employees[:excess] (first ones)
                # We only have IDs in DTO.
                candidates = firm_state.hr.employees[:excess]

                severance_weeks = getattr(config, 'severance_pay_weeks', 2) # DTO attributes might be snake_case
                # config is FirmConfigDTO.

                for emp_id in candidates:
                    emp_info = firm_state.hr.employees_data.get(emp_id, {})
                    current_wage = emp_info.get('wage', 1000) # Pennies
                    skill = emp_info.get('skill', 1.0)

                    # Severance calculation (pennies)
                    severance_pay = int(current_wage * severance_weeks * skill)

                    # Create FIRE order (Internal Market)
                    orders.append(Order(
                        agent_id=firm_state.id,
                        side='FIRE',
                        item_id='internal',
                        quantity=1,
                        price_pennies=severance_pay,
                        price_limit=float(severance_pay)/100.0,
                        market_id='internal',
                        target_agent_id=emp_id
                    ))
                    firing_ids.append(emp_id)

        # Check Hiring
        # Logic from RuleBasedFirmDecisionEngine._adjust_wages
        min_employees = getattr(config, 'firm_min_employees', 1)
        max_employees = getattr(config, 'firm_max_employees', 100)

        to_hire = 0
        if current_headcount < min_employees:
            to_hire = min_employees - current_headcount
        elif target_headcount > current_headcount and current_headcount < max_employees:
            to_hire = min(target_headcount - current_headcount, max_employees - current_headcount)

        if to_hire > 0:
            # Check Budget
            offered_wage = target_wage

            # Can we afford N hires?
            # Projected Cost = Current Wages + (N * Offered Wage)
            # Budget Plan labor_budget covers this?
            # Let's say labor_budget is for the *tick* (monthly/daily?)
            # Usually wages are paid periodically.
            # If labor_budget_pennies is the limit for *total* wage bill:
            if current_wage_bill + (to_hire * offered_wage) <= budget_plan.labor_budget_pennies:
                # Issue Buy Order
                orders.append(Order(
                    agent_id=firm_state.id,
                    side='BUY',
                    item_id='labor',
                    quantity=float(to_hire),
                    price_pennies=offered_wage,
                    price_limit=float(offered_wage)/100.0,
                    market_id='labor'
                ))
            else:
                # Reduce hires or skip
                pass

        return HRDecisionOutputDTO(
            hiring_orders=orders,
            firing_ids=firing_ids,
            wage_updates=wage_updates,
            target_headcount=target_headcount
        )

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
                    price=net_wage / 100.0,
                    market_id="labor",
                    transaction_type="wage",
                    time=current_time
                , total_pennies=net_wage)
                transactions.append(tx_wage)

                # Transaction 2: Income Tax (Firm -> Government) [Withholding]
                if income_tax > 0 and context.tax_policy:
                    tx_tax = Transaction(
                        buyer_id=firm_id, # Payer
                        seller_id=context.tax_policy.government_agent_id, # Payee
                        item_id="income_tax",
                        quantity=1.0,
                        price=income_tax / 100.0,
                        market_id="system",
                        transaction_type="tax",
                        time=current_time
                    , total_pennies=income_tax)
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
                price=severance_pay / 100.0,
                market_id="labor",
                transaction_type="severance",
                time=current_time
            , total_pennies=severance_pay)
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
            price=severance_pay / 100.0,
            market_id="system", # or labor?
            transaction_type="severance",
            time=current_time,
            currency=DEFAULT_CURRENCY
        , total_pennies=severance_pay)

    def finalize_firing(self, hr_state: HRState, employee_id: int):
        """
        Removes employee from state.
        Should be called after successful severance payment and employee.quit().
        """
        employee = next((e for e in hr_state.employees if e.id == employee_id), None)
        if employee:
             # employee.quit() is now handled by the Orchestrator
             self.remove_employee(hr_state, employee)
