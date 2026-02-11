from typing import Dict, Optional
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
        credit_score = application.borrower_profile.get("credit_score", 500)
        income = application.borrower_profile.get("income", 0) # pennies
        existing_debt = application.borrower_profile.get("total_debt", 0) # pennies

        is_approved = True
        rejection_reason = None
        risk_premium = 0.0

        # Debt-to-Income check
        if income > 0:
            dti = (existing_debt + application.amount_pennies) / (income * 12)
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
