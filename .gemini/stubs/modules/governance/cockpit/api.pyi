from _typeshed import Incomplete
from pydantic import BaseModel
from typing import Any, Literal, Protocol

CockpitCommandType: Incomplete

class CockpitCommand(BaseModel):
    """
    Represents a command from the Cockpit (frontend) to the Simulation.
    """
    type: CockpitCommandType
    payload: dict[str, Any]

class SetBaseRatePayload(BaseModel):
    """Payload for SET_BASE_RATE command."""
    rate: float

class SetTaxRatePayload(BaseModel):
    """Payload for SET_TAX_RATE command."""
    tax_type: Literal['corporate', 'income']
    rate: float

class ICommandService(Protocol):
    """
    Interface for the Command Service that manages the command queue.
    """
    def validate_command(self, command: CockpitCommand) -> bool:
        """Validates the command payload and type."""
    def enqueue_command(self, command: CockpitCommand) -> None:
        """Adds a valid command to the processing queue."""
