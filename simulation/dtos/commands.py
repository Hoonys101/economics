from dataclasses import dataclass
from typing import Any, Optional
from modules.system.api import OriginType

@dataclass
class GodCommandDTO:
    """
    Data Transfer Object for God-Mode commands.
    Used to intervene in the simulation state before the tick logic executes (Phase 0).
    """
    command_type: str  # "SET_PARAM", "INJECT_MONEY"
    target_domain: str # e.g., "household", "tax", "production"
    parameter_name: Optional[str] = None
    new_value: Any = None
    target_agent_id: Optional[int] = None
    amount: Optional[int] = None # Amount in pennies
    origin: OriginType = OriginType.GOD_MODE
