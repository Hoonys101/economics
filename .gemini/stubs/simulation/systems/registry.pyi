import logging
from _typeshed import Incomplete
from modules.finance.api import LienDTO as LienDTO
from modules.housing.api import IHousingService as IHousingService
from simulation.core_agents import Household as Household, Skill as Skill
from simulation.dtos.api import SimulationState as SimulationState
from simulation.firms import Firm as Firm
from simulation.models import Transaction as Transaction
from simulation.systems.api import IRegistry as IRegistry
from typing import Any
from uuid import UUID as UUID

logger: Incomplete

class Registry(IRegistry):
    """
    Updates non-financial state: Ownership, Inventory, Employment, Contracts.
    Extracted from TransactionProcessor.
    Refactored to delegate housing logic to HousingService.
    """
    logger: Incomplete
    housing_service: Incomplete
    def __init__(self, housing_service: IHousingService | None = None, logger: logging.Logger | None = None) -> None: ...
    def set_real_estate_units(self, units: list[Any]) -> None: ...
    def update_ownership(self, transaction: Transaction, buyer: Any, seller: Any, state: SimulationState) -> None:
        """
        Updates the registry based on the transaction type.
        """
