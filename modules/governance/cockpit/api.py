from __future__ import annotations
from typing import Dict, Any, Literal, Protocol, Optional, Union
from pydantic import BaseModel, Field

CockpitCommandType = Literal[
    "PAUSE",
    "RESUME",
    "STEP",
    "SET_BASE_RATE",
    "SET_TAX_RATE"
]

class CockpitCommand(BaseModel):
    """
    Represents a command from the Cockpit (frontend) to the Simulation.
    """
    type: CockpitCommandType
    payload: Dict[str, Any] = Field(default_factory=dict)

class SetBaseRatePayload(BaseModel):
    """Payload for SET_BASE_RATE command."""
    rate: float  # e.g., 0.05 for 5%

class SetTaxRatePayload(BaseModel):
    """Payload for SET_TAX_RATE command."""
    tax_type: Literal["corporate", "income"]
    rate: float

class ICommandService(Protocol):
    """
    Interface for the Command Service that manages the command queue.
    """
    def validate_command(self, command: CockpitCommand) -> bool:
        """Validates the command payload and type."""
        ...

    def enqueue_command(self, command: CockpitCommand) -> None:
        """Adds a valid command to the processing queue."""
        ...
