from _typeshed import Incomplete
from modules.government.constants import DEFAULT_INFRASTRUCTURE_INVESTMENT_COST as DEFAULT_INFRASTRUCTURE_INVESTMENT_COST
from modules.system.api import DEFAULT_CURRENCY as DEFAULT_CURRENCY
from simulation.agents.government import Government as Government
from simulation.models import Transaction
from typing import Any

logger: Incomplete

class InfrastructureManager:
    government: Incomplete
    config: Incomplete
    def __init__(self, government: Government) -> None: ...
    def invest_infrastructure(self, current_tick: int, households: list[Any] = None) -> list[Transaction]:
        """
        Refactored: Returns transactions instead of executing direct transfers.
        Side-effects (TFP Boost) are deferred via metadata.
        NOW DISTRIBUTES DIRECTLY TO HOUSEHOLDS (Public Works).
        """
