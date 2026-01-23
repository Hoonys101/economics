#
# File: simulation/systems/tech/api.py
#
from __future__ import annotations
from typing import List, Protocol, TypedDict, Set

# --- Data Transfer Objects (DTOs) ---


class FirmTechInfoDTO(TypedDict):
    """Minimal firm data required for technology diffusion."""

    id: int
    sector: str
    is_visionary: bool


class HouseholdEducationDTO(TypedDict):
    """Minimal household data required for human capital calculation."""

    is_active: bool
    education_level: float


# --- System Interface ---


class TechnologySystemAPI(Protocol):
    """
    Defines the public contract for the TechnologyManager.
    It operates on DTOs and primitive types, not full agent objects.
    """

    def update(
        self,
        current_tick: int,
        firms: List[FirmTechInfoDTO],
        human_capital_index: float,
    ) -> None:
        """
        Updates the state of technology diffusion.
        - Checks for new tech unlocks.
        - Processes the S-curve adoption for all active technologies.
        """
        ...

    def get_productivity_multiplier(self, firm_id: int) -> float:
        """
        Returns the total productivity multiplier for a given firm
        based on its adopted technologies.
        """
        ...

    def has_adopted(self, firm_id: int, tech_id: str) -> bool:
        """Checks if a firm has adopted a specific technology."""
        ...
