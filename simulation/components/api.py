from __future__ import annotations
from typing import Dict, Any, Optional, List, Protocol, TYPE_CHECKING
from dataclasses import dataclass, field
import random

if TYPE_CHECKING:
    from simulation.core_agents import Household

# ===================================================================================
# 1. Data Transfer Objects (DTOs)
# ===================================================================================

@dataclass
class DemographicsDTO:
    """
    A data transfer object for the demographic information of a household.
    """
    age: float
    gender: str
    generation: int
    parent_id: Optional[int] = None
    spouse_id: Optional[int] = None
    children_ids: List[int] = field(default_factory=list)

    @classmethod
    def from_component(cls, component: "IDemographicsComponent") -> "DemographicsDTO":
        """Creates a DTO from a component instance."""
        return cls(
            age=component.age,
            gender=component.gender,
            generation=component.generation,
            parent_id=component.parent_id,
            spouse_id=component.spouse_id,
            children_ids=component.children_ids.copy(),
        )


# ===================================================================================
# 2. Component Interfaces (Protocols)
# ===================================================================================

class IDemographicsComponent(Protocol):
    """
    An interface for a component that manages the demographic attributes and lifecycle
    (birth, aging, marriage, death) of a household. The Household class delegates
    demographic functionality to this interface.
    """

    # --- Properties (State Access) ---
    @property
    def owner(self) -> "Household":
        """The Household agent that owns this component."""
        ...

    @property
    def age(self) -> float:
        """The current age of the household."""
        ...

    @property
    def gender(self) -> str:
        """The gender of the household ('M' or 'F')."""
        ...

    @property
    def generation(self) -> int:
        """The generation of the household (starting from 0)."""
        ...

    @property
    def parent_id(self) -> Optional[int]:
        """The ID of the parent household."""
        ...

    @property
    def spouse_id(self) -> Optional[int]:
        """The ID of the spouse household."""
        ...

    @property
    def children_ids(self) -> List[int]:
        """A list of child household IDs."""
        ...

    @property
    def children_count(self) -> int:
        """The number of children."""
        ...

    # --- Lifecycle Methods (Lifecycle Management) ---
    def age_one_tick(self, current_tick: int) -> None:
        """
        Ages the household by one tick and handles any age-related state changes (e.g., death).
        """
        ...

    def handle_death(self, current_tick: int) -> bool:
        """
        Checks the conditions for death and returns the result after handling it.

        Returns:
            bool: True if the household has died, False otherwise.
        """
        ...

    def set_spouse(self, spouse_id: int) -> None:
        """Sets the spouse."""
        ...

    def add_child(self, child_id: int) -> None:
        """Adds a child."""
        ...

    def get_generational_similarity(self, talent_learning_rate_1: float, talent_learning_rate_2: float) -> float:
        """
        Calculates the generational/genetic similarity based on talent learning rates.
        Mainly used for spouse selection.
        """
        ...

    def create_offspring_demographics(self, new_id: int, current_tick: int) -> Dict[str, Any]:
        """
        Creates and returns the initial demographic data for an offspring.
        (Used for creating the offspring Household object)

        Args:
            new_id (int): The ID of the new offspring to be created.
            current_tick (int): The current simulation tick.

        Returns:
            Dict[str, Any]: A dictionary of the initial demographic attributes for the offspring.
        """
        ...
