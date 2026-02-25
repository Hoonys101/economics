from modules.firm.api import BudgetAllocationDTO as BudgetAllocationDTO, IBudgetGatekeeper as IBudgetGatekeeper, ObligationDTO as ObligationDTO, PaymentPriority as PaymentPriority
from modules.system.api import CurrencyCode as CurrencyCode, DEFAULT_CURRENCY as DEFAULT_CURRENCY

class BudgetGatekeeper(IBudgetGatekeeper):
    """
    Service responsible for enforcing liquidity constraints and payment priorities.
    """
    def allocate_budget(self, liquid_assets: dict[CurrencyCode, int], obligations: list[ObligationDTO]) -> BudgetAllocationDTO:
        """
        Filters obligations based on available liquidity and priority.
        Returns the approved allocation and insolvency status.
        """
