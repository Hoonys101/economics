from typing import TypedDict, Optional

class MortgageApplicationRequestDTO(TypedDict):
    """
    [TD-206] A precise data contract for applying for a mortgage.
    Sent by a saga or agent to the LoanMarket.
    Explicitly requires existing monthly debt payments to resolve DTI calculation ambiguity.
    """
    applicant_id: int
    requested_principal: float
    property_id: int # Context for the loan (though loan is on agent, lien is on property)
    property_value: float # For Loan-to-Value (LTV) calculation
    applicant_monthly_income: float
    existing_monthly_debt_payments: float # The SUM of all pre-existing monthly payments for other loans
    loan_term: int # Optional, defaults to market standard if not provided, usually 360 ticks

def calculate_monthly_loan_payment(principal: float, annual_interest_rate: float, term_months: float) -> float:
    """Calculates monthly payment using standard amortization formula."""
    if term_months <= 0:
        return 0.0

    monthly_rate = annual_interest_rate / 12.0
    if monthly_rate == 0:
        return principal / term_months

    return principal * (monthly_rate * (1 + monthly_rate)**term_months) / ((1 + monthly_rate)**term_months - 1)
