from typing import Any, Optional
import logging
from modules.finance.api import (
    ICreditScoringService,
    BorrowerProfileDTO,
    CreditAssessmentResultDTO
)

logger = logging.getLogger(__name__)

class CreditScoringService(ICreditScoringService):
    """
    Service for assessing creditworthiness based on DTI and LTV metrics.
    """

    def __init__(self, config_module: Any):
        self.config = config_module

    def assess_creditworthiness(self, profile: BorrowerProfileDTO, requested_loan_amount: float) -> CreditAssessmentResultDTO:
        """
        Evaluates a borrower's financial profile against lending criteria.
        """
        # Retrieve thresholds from config, with defaults
        max_dti = getattr(self.config, "MAX_DEBT_TO_INCOME_RATIO", 0.40)
        max_ltv = getattr(self.config, "MAX_LOAN_TO_VALUE_RATIO", 0.80)

        # 1. Debt-to-Income (DTI) Check
        # We assume gross_income and existing_debt_payments are normalized to the same period (e.g. monthly).
        if profile["gross_income"] <= 0:
            # If income is 0, they can't service any debt (unless they have assets, but DTI focuses on income)
            # However, if existing debt is 0, DTI is 0/0 = undefined.
            # But effectively infinite risk if income is 0.
            # Unless we consider asset depletion? DTI is strictly income-based.
            dti = float('inf')
            if profile["existing_debt_payments"] == 0:
                 dti = 0.0 # Technically 0 debt, but 0 income is still risky.
                 # But standard DTI calculation: Debt / Income.
                 # If Income is 0, ratio is undefined/infinite.
        else:
            dti = profile["existing_debt_payments"] / profile["gross_income"]

        if dti > max_dti:
            return CreditAssessmentResultDTO(
                is_approved=False,
                max_loan_amount=0.0,
                reason=f"DTI ratio {dti:.2f} exceeds limit {max_dti:.2f}"
            )

        # 2. Loan-to-Value (LTV) Check (if secured)
        # If collateral_value > 0, treat as secured.
        if profile["collateral_value"] > 0:
            ltv = requested_loan_amount / profile["collateral_value"]
            if ltv > max_ltv:
                 return CreditAssessmentResultDTO(
                    is_approved=False,
                    max_loan_amount=profile["collateral_value"] * max_ltv,
                    reason=f"LTV ratio {ltv:.2f} exceeds limit {max_ltv:.2f}"
                )

        # 3. Income Multiplier Check (Unsecured Cap)
        # If not secured (collateral <= 0), limit by income multiple (e.g. 3x monthly income)
        if profile["collateral_value"] <= 0:
            max_unsecured_multiplier = getattr(self.config, "MAX_UNSECURED_LOAN_INCOME_MULTIPLIER", 3.0)
            max_amount = profile["gross_income"] * max_unsecured_multiplier

            # Logic check: if income is 0, max_amount is 0.

            if requested_loan_amount > max_amount:
                 return CreditAssessmentResultDTO(
                    is_approved=False,
                    max_loan_amount=max_amount,
                    reason=f"Requested amount {requested_loan_amount:.2f} exceeds unsecured limit {max_amount:.2f}"
                )

        return CreditAssessmentResultDTO(
            is_approved=True,
            max_loan_amount=requested_loan_amount,
            reason=None
        )
