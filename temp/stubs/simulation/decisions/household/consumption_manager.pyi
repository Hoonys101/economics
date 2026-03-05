from simulation.decisions.household.api import ConsumptionContext as ConsumptionContext
from simulation.models import Order as Order
from simulation.schemas import HouseholdActionVector as HouseholdActionVector
from typing import Any

class ConsumptionManager:
    """
    Manages consumption logic (Maslow, Utility, Veblen, Hoarding).
    Refactored from AIDrivenHouseholdDecisionEngine.
    """
    def check_survival_override(self, household: Any, config: Any, market_snapshot: Any, current_time: int, logger: Any | None) -> tuple[list[Order], HouseholdActionVector] | None:
        """
        Phase 2: Survival Override.
        Checks if critical needs exceed threshold and triggers panic buying.
        """
    def decide_consumption(self, context: ConsumptionContext) -> list[Order]: ...
