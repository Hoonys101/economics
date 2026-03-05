from simulation.decisions.household.api import LaborContext as LaborContext
from simulation.models import Order as Order

class LaborManager:
    """
    Manages Labor decisions (Quit, Job Search, Reservation Wage).
    Refactored from AIDrivenHouseholdDecisionEngine.
    """
    def decide_labor(self, context: LaborContext) -> list[Order]: ...
