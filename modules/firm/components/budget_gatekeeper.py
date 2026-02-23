from __future__ import annotations
from typing import List, Dict, Any, Optional

from modules.system.api import CurrencyCode, DEFAULT_CURRENCY
from modules.firm.api import (
    IBudgetGatekeeper,
    ObligationDTO,
    BudgetAllocationDTO,
    PaymentPriority
)

class BudgetGatekeeper(IBudgetGatekeeper):
    """
    Service responsible for enforcing liquidity constraints and payment priorities.
    """

    def allocate_budget(
        self,
        liquid_assets: Dict[CurrencyCode, int],
        obligations: List[ObligationDTO]
    ) -> BudgetAllocationDTO:
        """
        Filters obligations based on available liquidity and priority.
        Returns the approved allocation and insolvency status.
        """
        # 1. Sort obligations by priority (ascending value = higher priority)
        sorted_obs = sorted(obligations, key=lambda x: x.priority)

        approved: List[ObligationDTO] = []
        rejected: List[ObligationDTO] = []

        # Working copy of balances to track depletion during allocation
        current_balances = liquid_assets.copy()

        for ob in sorted_obs:
            currency = ob.currency
            amount = ob.amount_pennies

            # Get available balance for this currency
            available = current_balances.get(currency, 0)

            if available >= amount:
                # Approve
                current_balances[currency] = available - amount
                approved.append(ob)
            else:
                # Reject
                rejected.append(ob)

        # 2. Insolvency Check
        # Check if any Mandatory Obligations (TAX or WAGE) were rejected
        mandatory_rejected = any(
            o.priority in [PaymentPriority.TAX, PaymentPriority.WAGE]
            for o in rejected
        )

        insolvency_reason = None
        if mandatory_rejected:
            reasons = []
            for o in rejected:
                if o.priority == PaymentPriority.TAX:
                    reasons.append("Unpaid Tax")
                elif o.priority == PaymentPriority.WAGE:
                    reasons.append("Unpaid Wage")
            insolvency_reason = f"Mandatory Obligations Rejected: {', '.join(set(reasons))}"

        # Calculate total approved amount (in default currency for summary, or strict sum?)
        # The DTO has `total_approved_amount_pennies`. Usually implies default currency total.
        # But we have multi-currency.
        # For simple summary, we can sum default currency amounts.
        total_approved = sum(o.amount_pennies for o in approved if o.currency == DEFAULT_CURRENCY)
        remaining_liquidity = current_balances.get(DEFAULT_CURRENCY, 0)

        return BudgetAllocationDTO(
            approved_obligations=approved,
            rejected_obligations=rejected,
            total_approved_amount_pennies=total_approved,
            remaining_liquidity_pennies=remaining_liquidity,
            is_insolvent=mandatory_rejected,
            insolvency_reason=insolvency_reason
        )
