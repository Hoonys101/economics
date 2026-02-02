from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional, Dict, Any

try:
    from pydantic.dataclasses import dataclass
except ImportError:
    from dataclasses import dataclass


# --- Data Transfer Objects (DTOs) ---

@dataclass(frozen=True)
class HouseholdHousingStateDTO:
    """A snapshot of a household's state relevant to housing decisions."""
    id: int
    assets: float
    income: float
    is_homeless: bool
    residing_property_id: Optional[int]
    owned_property_ids: List[int]
    needs: Dict[str, float]


@dataclass(frozen=True)
class RealEstateUnitDTO:
    """A snapshot of a real estate unit's state."""
    id: int
    owner_id: Optional[int]
    estimated_value: float
    rent_price: float
    for_sale_price: float
    on_market_for_rent: bool
    on_market_for_sale: bool


@dataclass(frozen=True)
class HousingMarketStateDTO:
    """A snapshot of the housing market."""
    units_for_sale: List[RealEstateUnitDTO]
    units_for_rent: List[RealEstateUnitDTO]


class HousingActionType(str, Enum):
    """Enumerates the possible housing decisions an agent can make."""
    STAY = "STAY"
    SEEK_RENTAL = "SEEK_RENTAL"
    SEEK_PURCHASE = "SEEK_PURCHASE"
    SELL_PROPERTY = "SELL_PROPERTY"


@dataclass(frozen=True)
class HousingDecisionDTO:
    """Represents the output of the housing planner."""
    agent_id: int
    action: HousingActionType
    target_unit_id: Optional[int] = None
    sell_unit_id: Optional[int] = None
    justification: str = ""


# --- Interfaces (Abstract Base Classes) ---

class IHousingPlanner(ABC):
    """
    Interface for the system that makes housing decisions for households.
    This contract ensures the planner is stateless and decoupled from the engine.
    """

    @abstractmethod
    def evaluate_and_decide(
        self,
        household: HouseholdHousingStateDTO,
        market: HousingMarketStateDTO,
        config: Any, # Using Any to avoid circular dependency with full config object
    ) -> HousingDecisionDTO:
        """
        Evaluates the household's situation and market conditions to recommend a housing action.

        Args:
            household: The current state of the household.
            market: The current state of the housing market.
            config: The simulation configuration object.

        Returns:
            A DTO representing the recommended decision.
        """
        ...
