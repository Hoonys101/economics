from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from dataclasses import dataclass, field
from modules.system.api import OriginType, AgentID

class JulesCommandType(Enum):
    """
    Categorization of commands issued by Jules.
    """
    INSPECT = "INSPECT"          # Read-only state extraction
    MODIFY_CONFIG = "MODIFY_CONFIG" # Configuration change via Registry
    INJECT_EVENT = "INJECT_EVENT"   # Scenario/Event injection
    FORCE_STATE = "FORCE_STATE"     # Direct agent state modification (Dangerous)
    SYSTEM_OP = "SYSTEM_OP"         # System-level operation (Save, Load, Pause)

@dataclass(frozen=True)
class JulesCommandDTO:
    """
    Standardized envelope for Jules commands.
    """
    command_id: str
    command_type: JulesCommandType
    target_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    origin: OriginType = OriginType.GOD_MODE
    timestamp: float = 0.0

@dataclass(frozen=True)
class JulesExecutionResultDTO:
    """
    Feedback loop for Jules commands.
    """
    command_id: str
    success: bool
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    affected_entities: List[str] = field(default_factory=list)
    execution_tick: int = 0

@dataclass(frozen=True)
class SimulationViewDTO:
    """
    Read-only view of the Simulation State.
    """
    tick: int
    view_type: str
    data: Dict[str, Any]

@runtime_checkable
class ISimulationSlicer(Protocol):
    """
    Protocol for creating safe, read-only views of the SimulationState.
    """
    def create_market_view(self, state: Any) -> SimulationViewDTO: ...
    def create_agent_view(self, state: Any, agent_ids: List[AgentID]) -> SimulationViewDTO: ...
    def create_system_view(self, state: Any) -> SimulationViewDTO: ...

@runtime_checkable
class IJulesOrchestrator(Protocol):
    """
    Interface for the central orchestration service handling Jules' interactions.
    """
    def execute_command(self, command: JulesCommandDTO) -> JulesExecutionResultDTO: ...
    def get_state_view(self, view_type: str, filters: Dict[str, Any]) -> SimulationViewDTO: ...
