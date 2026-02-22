from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
import logging
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode, MarketContextDTO
from modules.hr.api import IEmployeeDataProvider
from simulation.models import Transaction, Order
from simulation.components.state.firm_state_models import HRState
from simulation.dtos.hr_dtos import HRPayrollContextDTO, HRPayrollResultDTO, EmployeeUpdateDTO
from modules.firm.api import (
    HRDecisionInputDTO, HRDecisionOutputDTO, IHREngine,
    HRContextDTO, HRIntentDTO, IHRDepartment, AgentID,
    MarketSnapshotDTO
)

if TYPE_CHECKING:
    from modules.simulation.dtos.api import FirmConfigDTO, FirmStateDTO

logger = logging.getLogger(__name__)

class HREngine(IHREngine, IHRDepartment):
    """
    Stateless Engine for HR operations.
    Manages employees, calculates wages (skill + halo), and handles insolvency firing.
    """

    def decide_workforce(self, context: HRContextDTO) -> HRIntentDTO:
        """
        Pure function: HRContextDTO -> HRIntentDTO.
        Decides on hiring/firing targets and wage updates.
        """
        firing_ids: List[AgentID] = []
        wage_updates: Dict[AgentID, int] = {}
        hiring_target = 0

        target_headcount = context.target_workforce_count
        current_headcount = context.current_headcount

        # 1. Calculate Wages & Scale

        # Calculate Target Wage
        base_wage = context.labor_market_avg_wage
        sensitivity = 0.1
        max_premium = 2.0

        profit_history = context.profit_history
        avg_profit = sum(profit_history) / len(profit_history) if profit_history else 0.0

        profit_based_premium = avg_profit / (base_wage * 10.0) if base_wage > 0 else 0.0
        wage_premium = max(0, min(profit_based_premium * sensitivity, max_premium))

        # Wave 3: Adaptive Learning (TD-Error from previous hiring attempt)
        adaptive_premium = 0.0

        target_hires = context.target_hires_prev_tick
        actual_hires = context.hires_prev_tick
        last_offer = context.wage_offer_prev_tick
        hiring_deficit = 0

        if target_hires > 0:
            hiring_deficit = target_hires - actual_hires

            if hiring_deficit > 0:
                # Failed to hire enough -> Market is tight -> Increase wage
                # TD-Error > 0
                adaptive_premium = 0.1 * (hiring_deficit / target_hires) # Increase by up to 10%

            elif hiring_deficit <= 0 and actual_hires > 0:
                # Successfully hired all targets -> Maybe overpaying? -> Slight decrease or hold
                # TD-Error <= 0
                adaptive_premium = -0.01 # Decrease by 1% to test market

        # Combine premiums
        total_premium = wage_premium + adaptive_premium
        total_premium = max(0, min(total_premium, max_premium)) # Clamp

        # Base calculation on Market Avg OR Last Offer (if higher/relevant)
        if last_offer > base_wage and hiring_deficit > 0:
             # If we already offered above market and failed, base next offer on our last offer
             anchor_wage = last_offer
        else:
             anchor_wage = base_wage

        target_wage = int(anchor_wage * (1 + total_premium))

        # Wage Scaling: Update existing employees if underpaid
        current_wage_bill = 0
        for emp_id, current_wage in context.employee_wages.items():
            if current_wage < target_wage:
                wage_updates[emp_id] = target_wage
                current_wage_bill += target_wage
            else:
                current_wage_bill += current_wage

        # 2. Check Firing
        # "if current_employees > needed_labor + 1"
        if current_headcount > target_headcount + 1:
            excess = current_headcount - target_headcount
            excess = min(excess, max(0, current_headcount - 1))

            if excess > 0:
                # Find candidates (first ones in list for now)
                candidates = context.current_employees[:excess]
                firing_ids.extend(candidates)
                hiring_target = -excess # Negative indicates firing count if needed, but firing_ids is explicit

        # 3. Check Hiring
        min_employees = context.min_employees
        max_employees = context.max_employees

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
            if current_wage_bill + (to_hire * offered_wage) <= context.budget_pennies:
                hiring_target = to_hire
            else:
                # Reduce hires or skip
                # Simple logic: skip if over budget
                hiring_target = 0

        return HRIntentDTO(
            hiring_target=hiring_target,
            wage_updates=wage_updates,
            fire_employee_ids=firing_ids,
            hiring_wage_offer=target_wage
        )

    def manage_workforce(self, input_dto: HRDecisionInputDTO) -> HRDecisionOutputDTO:
        """
        Decides on hiring and firing based on production needs and budget constraints.
        Delegates to decide_workforce for core logic.
        """
        firm_state = input_dto.firm_snapshot
        config = input_dto.config

        # 1. Calculate Needed Labor (Logic remains here as Input Builder)
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

        # 2. Build Context
        context = self._build_context(input_dto, target_headcount)

        # 3. Execute Core Logic
        intent = self.decide_workforce(context)

        # 4. Map Intent to Legacy Output (Orders)
        orders: List[Order] = []

        # Firing Orders
        for emp_id in intent.fire_employee_ids:
            # We need skill/wage for severance calculation
            # It's in employees_data
            emp_info = firm_state.hr.employees_data.get(emp_id, {})
            current_wage = emp_info.get('wage', 1000)
            skill = emp_info.get('skill', 1.0)

            severance_weeks = context.severance_pay_weeks
            severance_pay = int(current_wage * severance_weeks * skill)

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

        # Hiring Orders
        if intent.hiring_target > 0:
            # Use wage from intent (Adaptive Learning result)
            offered_wage = intent.hiring_wage_offer

            orders.append(Order(
                agent_id=firm_state.id,
                side='BUY',
                item_id='labor',
                quantity=float(intent.hiring_target),
                price_pennies=offered_wage,
                price_limit=float(offered_wage)/100.0,
                market_id='labor',
                metadata={
                    'major': context.specialization,
                    'required_education': 0 # Dynamic logic can be added here
                }
            ))

        return HRDecisionOutputDTO(
            hiring_orders=orders,
            firing_ids=intent.fire_employee_ids, # IDs, already list[int] compatible (AgentID is NewType(int))
            wage_updates={int(k): v for k, v in intent.wage_updates.items()}, # Cast AgentID to int key
            target_headcount=target_headcount
        )

    def _build_context(self, input_dto: HRDecisionInputDTO, target_headcount: int) -> HRContextDTO:
        firm_state = input_dto.firm_snapshot
        config = input_dto.config
        hr_state = firm_state.hr

        current_employees = [AgentID(e_id) for e_id in hr_state.employees]
        employees_data = hr_state.employees_data

        employee_wages = {AgentID(k): v.get('wage', 0) for k, v in employees_data.items()}
        employee_skills = {AgentID(k): v.get('skill', 1.0) for k, v in employees_data.items()}

        return HRContextDTO(
            firm_id=AgentID(firm_state.id),
            tick=input_dto.current_tick,
            budget_pennies=input_dto.budget_plan.labor_budget_pennies,
            market_snapshot=MarketSnapshotDTO(tick=0, market_signals={}, market_data={}), # Dummy if not needed inside decide
            available_cash_pennies=0, # Not used
            is_solvent=True,

            current_employees=current_employees,
            current_headcount=len(current_employees),
            employee_wages=employee_wages,
            employee_skills=employee_skills,
            target_workforce_count=target_headcount,
            labor_market_avg_wage=input_dto.labor_market_avg_wage,
            marginal_labor_productivity=0.0, # Not used in current logic
            happiness_avg=0.0, # Not used

            profit_history=firm_state.finance.profit_history,

            min_employees=getattr(config, 'firm_min_employees', 1),
            max_employees=getattr(config, 'firm_max_employees', 100),
            severance_pay_weeks=getattr(config, 'severance_pay_weeks', 2),
            specialization=firm_state.production.specialization,
            major=getattr(firm_state.production, 'major', 'GENERAL'), # Phase 4.1

            # Adaptive Learning History
            hires_prev_tick=firm_state.hr.hires_prev_tick,
            target_hires_prev_tick=firm_state.hr.target_hires_prev_tick,
            wage_offer_prev_tick=firm_state.hr.wage_offer_prev_tick
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
        hr_state.hires_this_tick += 1
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
