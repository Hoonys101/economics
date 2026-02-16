from typing import Dict, Optional, Any
import uuid
from modules.finance.engine_api import (
    ILoanRiskEngine, LoanApplicationDTO, FinancialLedgerDTO, LoanDecisionDTO
)

class LoanRiskEngine(ILoanRiskEngine):
    """
    Stateless engine to assess loan applications.
    MIGRATION: Uses integer pennies.
    """

    def assess(
        self,
        application: LoanApplicationDTO,
        ledger: FinancialLedgerDTO
    ) -> LoanDecisionDTO:

        base_rate = 0.03
        if ledger.banks:
            base_rate = next(iter(ledger.banks.values())).base_rate

        # 2. Analyze Profile (Values are int pennies)
        # MIGRATION: Support updated BorrowerProfileDTO structure (float fields).
        # Robustly handle profile as Dict or Object to satisfy reviews and future-proofing.

        profile: Any = application.borrower_profile

        def get_field(key: str, default: Any = None) -> Any:
            if hasattr(profile, "get"):
                return profile.get(key, default)
            return getattr(profile, key, default)

        credit_score_val = get_field("credit_score")
        if credit_score_val is None:
             credit_score_val = 500
        credit_score = float(credit_score_val)

        # Retrieve income (float pennies)
        income = float(get_field("gross_income", 0.0))
        if income == 0.0:
             # Fallback to legacy key
             income = float(get_field("income", 0.0))

        # Retrieve existing debt stock (float pennies)
        # New DTO lacks total_debt stock, so we default to 0.0 unless provided (legacy).
        existing_debt = float(get_field("total_debt", 0.0))

        is_approved = True
        rejection_reason = None
        risk_premium = 0.0

        # Debt-to-Income check (Leverage Ratio: Total Debt / Annual Income)
        # We include the *new* loan amount in the numerator.
        if income > 0:
            dti = (existing_debt + float(application.amount_pennies)) / (income * 12.0)
            if dti > 5.0:
                is_approved = False
                rejection_reason = "Debt-to-Income too high"

        # Credit Score check
        if credit_score < 300:
             is_approved = False
             rejection_reason = "Credit Score too low"
        elif credit_score < 600:
             risk_premium = 0.05
        else:
             risk_premium = 0.02

        final_rate = base_rate + risk_premium

        return LoanDecisionDTO(
            is_approved=is_approved,
            interest_rate=final_rate,
            rejection_reason=rejection_reason
        )
