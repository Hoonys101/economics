from __future__ import annotations
from typing import Any, Dict, Protocol, runtime_checkable
from dataclasses import dataclass
from enum import Enum

# Using system API definitions to avoid circular dependencies
from modules.system.api import AgentID

class LifecycleEventType(Enum):
    BORN = "BORN"
    BANKRUPT = "BANKRUPT"
    STARVED = "STARVED"
    LIQUIDATED = "LIQUIDATED"

@dataclass(frozen=True)
class AgentRegistrationDTO:
    """DTO containing pure data for agent instantiation, avoiding God Classes."""
    agent_type: str
    initial_assets: Dict[str, int]
    metadata: Dict[str, Any]

@dataclass(frozen=True)
class AgentDeactivationEventDTO:
    """DTO broadcasted when an agent is removed from active simulation."""
    agent_id: AgentID
    reason: LifecycleEventType
    tick: int
    unresolved_liabilities: int

@runtime_checkable
class IAgentLifecycleManager(Protocol):
    """
    Protocol decoupling lifecycle orchestration from the SimulationState.
    Coordinates atomic operations across IAgentRegistry and IMonetaryLedger.
    """
    def register_firm(self, dto: AgentRegistrationDTO) -> AgentID:
        """Atomically registers a firm in the registry and instantiates its ledger account."""
        ...

    def register_household(self, dto: AgentRegistrationDTO) -> AgentID:
        """Atomically registers a household in the registry and instantiates its ledger account."""
        ...

    def deactivate_agent(self, agent_id: AgentID, reason: LifecycleEventType) -> AgentDeactivationEventDTO:
        """
        Safely removes an agent from the active economy.
        Must cancel active orders, terminate pending sagas, and trigger asset liquidation.
        """
        ...

    def process_starvation(self, household_id: AgentID, current_tick: int) -> None:
        """Handles basic food starvation for a household."""
        ...
