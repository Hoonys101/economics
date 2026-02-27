from _typeshed import Incomplete
from modules.government.api import IGovernmentDecisionEngine as IGovernmentDecisionEngine
from modules.government.dtos import GovernmentStateDTO as GovernmentStateDTO, PolicyActionDTO as PolicyActionDTO, PolicyDecisionDTO as PolicyDecisionDTO
from modules.government.policies.adaptive_gov_brain import AdaptiveGovBrain as AdaptiveGovBrain
from simulation.ai.enums import EconomicSchool as EconomicSchool
from simulation.dtos.api import MarketSnapshotDTO as MarketSnapshotDTO
from typing import Any

logger: Incomplete

class GovernmentDecisionEngine(IGovernmentDecisionEngine):
    """
    [DEPRECATED] Stateless engine that decides on government policy actions.
    Replaced by FiscalEngine for Fiscal Policy.
    It delegates the specific logic to a strategy (e.g., Taylor Rule, AI).
    """
    config: Incomplete
    strategy_mode: Incomplete
    brain: Incomplete
    def __init__(self, config_module: Any, strategy_mode: str = 'TAYLOR_RULE') -> None: ...
    def decide(self, state: GovernmentStateDTO, market_snapshot: MarketSnapshotDTO, central_bank: Any) -> PolicyDecisionDTO:
        """
        Decides on a policy action based on current state and market data.
        """
