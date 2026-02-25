from modules.system.api import AgentID as AgentID, IAgent as IAgent, IAgentRegistry as IAgentRegistry, IConfigurationRegistry as IConfigurationRegistry, IGlobalRegistry as IGlobalRegistry, ISystemAgentRegistry as ISystemAgentRegistry, OriginType as OriginType, RegistryEntry as RegistryEntry, RegistryObserver as RegistryObserver, RegistryValueDTO as RegistryValueDTO
from modules.system.services.schema_loader import SchemaLoader as SchemaLoader
from simulation.agents import Agent as Agent
from simulation.dtos.api import SimulationState as SimulationState
from simulation.dtos.registry_dtos import ParameterSchemaDTO
from typing import Any

class AgentRegistry(IAgentRegistry, ISystemAgentRegistry):
    def __init__(self) -> None: ...
    def set_state(self, state: SimulationState) -> None: ...
    def register(self, agent: Agent) -> None:
        """
        Registers an agent into the registry's state.
        Ensures atomic registration visibility.
        """
    def register_system_agent(self, agent: IAgent) -> None:
        """Registers a system agent bypassing standard initialization constraints."""
    def get_system_agent(self, agent_id: AgentID) -> IAgent | None:
        """Retrieves a system agent, supporting ID 0."""
    def get_agent(self, agent_id: Any) -> Agent | None: ...
    def get_all_financial_agents(self) -> list[Any]: ...
    def get_all_agents(self) -> list[Any]: ...
    def is_agent_active(self, agent_id: int) -> bool:
        """Returns True if the agent exists and has not been marked INACTIVE/DEAD."""

class GlobalRegistry(IGlobalRegistry, IConfigurationRegistry):
    """
    Central repository for simulation parameters with priority and locking mechanisms.
    FOUND-01: Implements Origin-based access control and observer pattern using Layered Storage.
    """
    def __init__(self, initial_data: dict[str, Any] | None = None) -> None: ...
    def get(self, key: str, default: Any = None) -> Any: ...
    def set(self, key: str, value: Any, origin: OriginType = ...) -> bool: ...
    def lock(self, key: str) -> None:
        """Locks a specific parameter with God-Mode authority."""
    def unlock(self, key: str) -> None:
        """Unlocks a parameter, allowing updates from equal or higher origin."""
    def subscribe(self, observer: RegistryObserver, keys: list[str] | None = None) -> None: ...
    def snapshot(self) -> dict[str, RegistryValueDTO]:
        """Returns snapshot of ACTIVE entries."""
    def get_metadata(self, key: str) -> ParameterSchemaDTO | None: ...
    def get_entry(self, key: str) -> RegistryValueDTO | None: ...
    def delete_entry(self, key: str) -> bool:
        """Deletes an entry completely (for rollback purposes)."""
    def delete_layer(self, key: str, origin: OriginType) -> bool:
        """Removes a specific layer for a key, exposing lower layers if any."""
    def restore_entry(self, key: str, entry: RegistryValueDTO) -> bool:
        """Restores a full entry state (for rollback purposes)."""
    def reset_to_defaults(self) -> None:
        """
        Resets all configuration values to their SYSTEM or CONFIG defaults,
        clearing USER overrides.
        """
    def migrate_from_dict(self, data: dict[str, Any]) -> None:
        """
        Migrates a dictionary of configuration values into the registry.
        Assumes keys are 'domain.key' or simple keys.
        """
