from _typeshed import Incomplete
from simulation.core_agents import Household as Household
from typing import Any

logger: Incomplete

class GenerationalWealthAudit:
    """
    WO-058: Generational Wealth Audit
    Calculates and logs the distribution of wealth across generations.
    """
    config_module: Incomplete
    logger: Incomplete
    def __init__(self, config_module: Any) -> None: ...
    def run_audit(self, agents: list[Household], current_tick: int) -> None:
        """
        Calculates and logs the wealth distribution across generations.

        Args:
            agents: A list of all household agents in the simulation.
            current_tick: The current simulation tick.
        """
