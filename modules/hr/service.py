from __future__ import annotations
from typing import List, TYPE_CHECKING
from modules.hr.api import IHRService
from modules.common.dtos import Claim

if TYPE_CHECKING:
    from simulation.firms import Firm

class HRService(IHRService):
    def calculate_liquidation_employee_claims(self, firm: Firm, current_tick: int) -> List[Claim]:
        claims = []
        ticks_per_year = getattr(firm.config, "ticks_per_year", 365)

        # A. Unpaid Wages
        # Cap at 3 months (ticks_per_year / 4)
        wage_cutoff_tick = current_tick - (ticks_per_year // 4)
        if hasattr(firm.hr, 'unpaid_wages'):
            for employee_id, wage_records in firm.hr.unpaid_wages.items():
                # Filter strict 3-month window
                total_unpaid = sum(amount for tick, amount in wage_records if tick >= wage_cutoff_tick)
                if total_unpaid > 0:
                    claims.append(Claim(
                        creditor_id=employee_id,
                        amount=total_unpaid,
                        tier=1,
                        description="Unpaid Wages"
                    ))

        # B. Severance Pay
        # "Accrued severance pay for all employees over the last 3 years of service."
        accrual_rate_weeks = getattr(firm.config, "severance_pay_weeks", 2.0)
        ticks_per_week = ticks_per_year / 52.0

        for employee in firm.hr.employees:
            # Calculate Tenure
            start_tick = getattr(employee._econ_state, 'employment_start_tick', -1)
            tenure_years = 0.0
            if start_tick >= 0:
                tenure_years = (current_tick - start_tick) / ticks_per_year

            # Cap at 3 years
            effective_tenure = min(tenure_years, 3.0)

            # Calculate Severance Amount
            current_wage = firm.hr.employee_wages.get(employee.id, 0.0)
            if current_wage > 0:
                # Formula: Years * Weeks/Year * Ticks/Week * Wage/Tick
                severance_ticks = effective_tenure * accrual_rate_weeks * ticks_per_week
                severance_amount = severance_ticks * current_wage

                if severance_amount > 0:
                    claims.append(Claim(
                        creditor_id=employee.id,
                        amount=severance_amount,
                        tier=1,
                        description=f"Severance ({effective_tenure:.2f} yr)"
                    ))

        return claims
