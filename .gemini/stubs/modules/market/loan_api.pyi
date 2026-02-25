from _typeshed import Incomplete
from modules.finance.api import MortgageApplicationDTO as MortgageApplicationDTO
from typing import Any

logger: Incomplete
MortgageApplicationRequestDTO = MortgageApplicationDTO

def calculate_monthly_loan_payment(principal: float, annual_interest_rate: float, term_months: float) -> float:
    """Calculates monthly payment using standard amortization formula."""
def calculate_monthly_income(current_wage_per_tick: float, ticks_per_year: int) -> float:
    """Calculates monthly income from tick-based wage."""
def calculate_total_monthly_debt_payments(bank_service: Any, agent_id: int, ticks_per_year: int) -> float:
    """
    Calculates the total existing monthly debt payments for an agent by querying the bank.
    Centralizes logic to avoid duplication between Saga Handler and Household Mixin.
    """
