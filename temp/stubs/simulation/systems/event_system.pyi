from _typeshed import Incomplete
from simulation.agents.central_bank import CentralBank as CentralBank
from simulation.agents.government import Government as Government
from simulation.dtos.scenario import StressScenarioConfig as StressScenarioConfig
from simulation.finance.api import IMintingSystem as IMintingSystem, ISettlementSystem as ISettlementSystem
from simulation.systems.api import EventContext as EventContext, IEventSystem as IEventSystem
from typing import Any

logger: Incomplete

class EventSystem(IEventSystem):
    """
    Manages scheduled events like Inflation Shock and Recession Shock.
    """
    config: Incomplete
    settlement_system: Incomplete
    def __init__(self, config: Any, settlement_system: ISettlementSystem) -> None: ...
    def execute_scheduled_events(self, time: int, context: EventContext, config: StressScenarioConfig) -> None:
        """
        Executes stress scenario triggers based on the provided configuration.
        """
