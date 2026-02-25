from _typeshed import Incomplete
from modules.government.dtos import GovernmentSensoryDTO as GovernmentSensoryDTO
from simulation.interfaces.policy_interface import IGovernmentPolicy as IGovernmentPolicy
from typing import Any, Deque

class TaylorRulePolicy(IGovernmentPolicy):
    """
    WO-056: Taylor Rule based policy engine.
    Responsible for formula-based decisions and shadow mode logging.
    """
    config: Incomplete
    price_history_shadow: Deque[float]
    potential_gdp: float
    def __init__(self, config_module: Any) -> None: ...
    def decide(self, government: Any, sensory_data: GovernmentSensoryDTO | None, current_tick: int, central_bank: Any = None) -> dict[str, Any]: ...
