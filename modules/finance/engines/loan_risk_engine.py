from typing import Dict, Optional
import uuid
from modules.finance.engine_api import (
    ILoanRiskEngine, LoanApplicationDTO, FinancialLedgerDTO, LoanDecisionDTO
)

class LoanRiskEngine(ILoanRiskEngine):
    """
    Stateless engine to assess loan applications.
    """

    def assess(
        self,
        application: LoanApplicationDTO,
        ledger: FinancialLedgerDTO
    ) -> LoanDecisionDTO:

        # 1. Get Base Rate (Assume average of banks or specific bank if we knew which one)
        # For simplicity, we can take the first bank's rate or a default.
        # Ideally, application should specify lender_id.
        # Let's assume lender_id is implicit or we pick a standard rate.
        # Wait, the DTO doesn't have lender_id in LoanApplicationDTO?
        # It should. I added it in my thought process but maybe missed it in the file?
        # Let's check LoanApplicationDTO definition in engine_api.py.
        # It has borrower_id, amount, borrower_profile. No lender_id.
        # I'll assume we use a system-wide or average base rate, or maybe pass it in context.
        # But `ledger` has banks.

        base_rate = 0.03
        if ledger.banks:
            # Just pick the first one for now as a reference
            base_rate = next(iter(ledger.banks.values())).base_rate

        # 2. Analyze Profile
        credit_score = application.borrower_profile.get("credit_score", 500)
        income = application.borrower_profile.get("income", 0.0)
        existing_debt = application.borrower_profile.get("total_debt", 0.0)

        # Simple Logic
        is_approved = True
        rejection_reason = None
        risk_premium = 0.0

        # Debt-to-Income check (if income known)
        if income > 0:
            dti = (existing_debt + application.amount) / (income * 12) # Annualized?
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
