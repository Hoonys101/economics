from _typeshed import Incomplete
from simulation.dtos.scenario import StressScenarioConfig as StressScenarioConfig
from simulation.models import Transaction as Transaction
from simulation.systems.api import CommerceContext as CommerceContext, ICommerceSystem as ICommerceSystem
from typing import Any

logger: Incomplete

class CommerceSystem(ICommerceSystem):
    """
    Orchestrates the consumption and leisure phase of the tick.
    """
    config: Incomplete
    def __init__(self, config: Any) -> None: ...
    def plan_consumption_and_leisure(self, context: CommerceContext, scenario_config: StressScenarioConfig | None = None) -> tuple[dict[int, dict[str, Any]], list[Transaction]]:
        """
        Phase 1: Decisions.
        Determines desired consumption and generates transactions for Fast Purchase.
        Returns (PlannedConsumptionMap, Transactions).
        """
    def finalize_consumption_and_leisure(self, context: CommerceContext, planned_consumptions: dict[int, dict[str, Any]]) -> dict[int, float]:
        """
        Phase 4: Lifecycle Effects.
        Executes consumption from inventory and applies leisure effects.
        """
