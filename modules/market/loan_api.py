from typing import TypedDict, Optional, Any
import logging
from modules.finance.api import MortgageApplicationDTO

logger = logging.getLogger(__name__)

# [TD-223] Unification: Using MortgageApplicationDTO from finance.api
# MortgageApplicationRequestDTO has been removed/aliased.
# We aliasing it here to support step-by-step migration, but it should be deprecated.
MortgageApplicationRequestDTO = MortgageApplicationDTO

def calculate_monthly_loan_payment(principal: float, annual_interest_rate: float, term_months: float) -> float:
    """Calculates monthly payment using standard amortization formula."""
    if term_months <= 0:
        return 0.0

    monthly_rate = annual_interest_rate / 12.0
    if monthly_rate == 0:
        return principal / term_months

    return principal * (monthly_rate * (1 + monthly_rate)**term_months) / ((1 + monthly_rate)**term_months - 1)

def calculate_monthly_income(current_wage_per_tick: float, ticks_per_year: int) -> float:
    """Calculates monthly income from tick-based wage."""
    if ticks_per_year <= 0:
        return 0.0
    return (current_wage_per_tick * ticks_per_year) / 12.0

def calculate_total_monthly_debt_payments(bank_service: Any, agent_id: int, ticks_per_year: int) -> float:
    """
    Calculates the total existing monthly debt payments for an agent by querying the bank.
    Centralizes logic to avoid duplication between Saga Handler and Household Mixin.
    """
    total_payment = 0.0

    if not bank_service:
        return 0.0

    try:
        if not hasattr(bank_service, 'get_debt_status'):
             logger.warning(f"Bank service {bank_service} does not support get_debt_status")
             return 0.0

        debt_status = bank_service.get_debt_status(agent_id)
        if debt_status and 'loans' in debt_status:
            for loan in debt_status['loans']:
                principal = loan['original_amount']
                interest_rate = loan['interest_rate']
                start = loan['origination_tick']
                end = loan.get('due_tick')

                if end and start is not None:
                    term_ticks = end - start
                    if term_ticks > 0:
                        ticks_per_month = ticks_per_year / 12.0
                        term_months = term_ticks / ticks_per_month

                        pmt = calculate_monthly_loan_payment(principal, interest_rate, term_months)
                        total_payment += pmt
    except Exception as e:
        logger.warning(f"Failed to calculate total debt payments for agent {agent_id}: {e}")
        # Return partial sum or 0? 0 might be dangerous (approving bad loans).
        # But partial sum is also dangerous.
        # Given this is a getter, we return what we found, logging the error.

    return total_payment
