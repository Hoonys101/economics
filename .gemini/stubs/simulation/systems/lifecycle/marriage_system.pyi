import logging
from _typeshed import Incomplete
from modules.common.interfaces import IPropertyOwner as IPropertyOwner
from modules.finance.api import IFinancialAgent as IFinancialAgent, ISettlementSystem as ISettlementSystem
from simulation.core_agents import Household as Household
from simulation.dtos.api import SimulationState as SimulationState
from simulation.models import Transaction as Transaction

logger: Incomplete

class MarriageSystem:
    '''
    Manages the marriage market and household mergers.
    Implements the "Asset Merger & Dependent Spouse" model.
    '''
    settlement_system: Incomplete
    logger: Incomplete
    marriage_min_age: float
    marriage_max_age: float
    marriage_chance: float
    def __init__(self, settlement_system: ISettlementSystem, logger: logging.Logger) -> None: ...
    def execute(self, state: SimulationState) -> list[Transaction]:
        """
        Identifies eligible singles, matches them, and executes mergers.
        Returns any financial transactions generated (e.g. dowry/transfer).
        """
