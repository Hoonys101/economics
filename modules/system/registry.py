from __future__ import annotations
from typing import Optional, Any, TYPE_CHECKING, Dict, List
from modules.system.api import IAgentRegistry, IGlobalRegistry, IConfigurationRegistry, OriginType, RegistryValueDTO, RegistryObserver, RegistryEntry, ISystemAgentRegistry, IAgent, AgentID
from modules.system.services.schema_loader import SchemaLoader
from simulation.dtos.registry_dtos import ParameterSchemaDTO

if TYPE_CHECKING:
    from simulation.agents import Agent
    from simulation.dtos.api import SimulationState

class AgentRegistry(IAgentRegistry, ISystemAgentRegistry):
    def __init__(self):
        self._state: Optional[SimulationState] = None

    def set_state(self, state: SimulationState) -> None:
        self._state = state

    def register(self, agent: Agent) -> None:
        """
        Registers an agent into the registry's state.
        Ensures atomic registration visibility.
        """
        if self._state is not None:
            self._state.agents[agent.id] = agent

    def register_system_agent(self, agent: IAgent) -> None:
        """Registers a system agent bypassing standard initialization constraints."""
        if self._state is not None:
            self._state.agents[agent.id] = agent

    def get_system_agent(self, agent_id: AgentID) -> Optional[IAgent]:
        """Retrieves a system agent, supporting ID 0."""
        if self._state is None:
            return None
        return self._state.agents.get(agent_id)

    def get_agent(self, agent_id: Any) -> Optional[Agent]:
        if agent_id is None:
            return None
        if self._state is None:
            return None
        agent = self._state.agents.get(agent_id)
        if agent is not None:
             return agent

        # Check Estate Registry
        if hasattr(self._state, 'estate_registry') and self._state.estate_registry:
             return self._state.estate_registry.get_agent(agent_id)

        return None

    def get_all_financial_agents(self) -> List[Any]:
        if self._state is None:
            return []
        # Since all system agents (Government, Central Bank, etc) are now explicitly registered
        # in state.agents by SimulationInitializer, we can simply return values.
        return list(self._state.agents.values())

    def get_all_agents(self) -> List[Any]:
        if self._state is None:
            return []
        return list(self._state.agents.values())

    def is_agent_active(self, agent_id: int) -> bool:
        """Returns True if the agent exists and has not been marked INACTIVE/DEAD."""
        if self._state is None:
            return False
        agent = self._state.agents.get(agent_id)
        if not agent:
            return False
        return getattr(agent, "is_active", False)

class GlobalRegistry(IGlobalRegistry, IConfigurationRegistry):
    """
    Central repository for simulation parameters with priority and locking mechanisms.
    FOUND-01: Implements Origin-based access control and observer pattern using Layered Storage.
    """
    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        # Layered storage: Key -> {Origin -> Entry}
        self._layers: Dict[str, Dict[OriginType, RegistryValueDTO]] = {}
        self._observers: List[RegistryObserver] = []
        self._key_observers: Dict[str, List[RegistryObserver]] = {}
        # Placeholder for scheduler injection (Phase 0 Intercept)
        self._scheduler = None
        # Load metadata schema on initialization
        self._metadata_map: Dict[str, ParameterSchemaDTO] = {}
        self._load_metadata()

        if initial_data:
            self.migrate_from_dict(initial_data)

    def _load_metadata(self) -> None:
        schemas = SchemaLoader.load_schema()
        if isinstance(schemas, list):
            for schema in schemas:
                # schema is a dict (or now Pydantic if SchemaLoader was updated? No, SchemaLoader returns dict or list of dicts)
                # ParameterSchemaDTO is now Pydantic.
                # SchemaLoader currently returns raw dicts from YAML.
                # We can access them as dicts.
                if isinstance(schema, dict) and 'key' in schema:
                    # Validate with Pydantic
                    try:
                        dto = ParameterSchemaDTO(**schema)
                        self._metadata_map[dto.key] = dto
                    except Exception as e:
                         # Log error but continue
                         pass

    def _get_active_entry(self, key: str) -> Optional[RegistryValueDTO]:
        layers = self._layers.get(key)
        if not layers:
            return None
        # Return entry with highest origin priority
        max_origin = max(layers.keys(), key=lambda o: o.value)
        return layers[max_origin]

    def get(self, key: str, default: Any = None) -> Any:
        entry = self._get_active_entry(key)
        return entry.value if entry else default

    def set(self, key: str, value: Any, origin: OriginType = OriginType.CONFIG) -> bool:
        active_entry = self._get_active_entry(key)

        # 1. Authority Check
        if active_entry:
            # If locked, only GOD_MODE (or equivalent high privilege) can modify
            if active_entry.is_locked:
                if origin < OriginType.GOD_MODE:
                     raise PermissionError(f"Target '{key}' is locked by {active_entry.origin.name}")

            # Priority Check: Lower origin cannot overwrite higher active origin
            if origin < active_entry.origin:
                return False

        # 2. Phase 0 Intercept (TODO: Implement when Scheduler is available)
        # ...

        # 3. Update Layer
        is_locked = (origin == OriginType.GOD_MODE)

        # Determine Domain (Default "global" or parse from key)
        domain = "global"
        if "." in key:
            domain = key.split(".")[0]

        new_entry = RegistryValueDTO(
            key=key,
            value=value,
            domain=domain,
            origin=origin,
            is_locked=is_locked,
            last_updated_tick=0 # TODO: Inject scheduler.current_tick
        )

        if key not in self._layers:
            self._layers[key] = {}

        self._layers[key][origin] = new_entry

        # Notify if the active value effectively changed or if it was the active layer updated
        current_active = self._get_active_entry(key)
        if current_active and current_active.origin == origin:
             self._notify(key, value, origin)

        return True

    def lock(self, key: str) -> None:
        """Locks a specific parameter with God-Mode authority."""
        # Locking is essentially setting a GOD_MODE entry with lock=True
        # We preserve the *current active value* but elevate it to GOD_MODE
        active = self._get_active_entry(key)
        value = active.value if active else None

        # If no value exists, we can't lock 'nothing', or we lock 'None'?
        if active:
            self.set(key, value, OriginType.GOD_MODE)
            # Ensure lock flag is set (set() does this for GOD_MODE)
            # Note: set() above sets is_locked=True for GOD_MODE.

    def unlock(self, key: str) -> None:
        """Unlocks a parameter, allowing updates from equal or higher origin."""
        # Unlocking means removing the lock.
        # If the lock was at GOD_MODE layer, we might want to downgrade it or just unset is_locked.
        # But if we just unset is_locked, it's still GOD_MODE origin (highest).
        # Usually unlock implies removing the GOD_MODE override?
        # Or just allowing changes.
        # If I remove the GOD_MODE layer, it reverts to USER/CONFIG.
        if key in self._layers and OriginType.GOD_MODE in self._layers[key]:
            del self._layers[key][OriginType.GOD_MODE]
            # Notify potential change
            active = self._get_active_entry(key)
            if active:
                self._notify(key, active.value, active.origin)

    def subscribe(self, observer: RegistryObserver, keys: Optional[List[str]] = None) -> None:
        if keys is None:
            self._observers.append(observer)
        else:
            for key in keys:
                if key not in self._key_observers:
                    self._key_observers[key] = []
                self._key_observers[key].append(observer)

    def _notify(self, key: str, value: Any, origin: OriginType) -> None:
        # Notify global observers
        for observer in self._observers:
            observer.on_registry_update(key, value, origin)

        # Notify key-specific observers
        if key in self._key_observers:
            for observer in self._key_observers[key]:
                observer.on_registry_update(key, value, origin)

    def snapshot(self) -> Dict[str, RegistryValueDTO]:
        """Returns snapshot of ACTIVE entries."""
        result = {}
        for key in self._layers:
            entry = self._get_active_entry(key)
            if entry:
                result[key] = entry
        return result

    def get_metadata(self, key: str) -> Optional[ParameterSchemaDTO]:
        return self._metadata_map.get(key)

    def get_entry(self, key: str) -> Optional[RegistryValueDTO]:
        return self._get_active_entry(key)

    def delete_entry(self, key: str) -> bool:
        """Deletes an entry completely (for rollback purposes)."""
        if key in self._layers:
            del self._layers[key]
            return True
        return False

    def delete_layer(self, key: str, origin: OriginType) -> bool:
        """Removes a specific layer for a key, exposing lower layers if any."""
        if key in self._layers and origin in self._layers[key]:
            del self._layers[key][origin]
            # Notify potential change
            active = self._get_active_entry(key)
            val = active.value if active else None
            origin_active = active.origin if active else OriginType.SYSTEM
            self._notify(key, val, origin_active)
            return True
        return False

    def restore_entry(self, key: str, entry: RegistryValueDTO) -> bool:
        """Restores a full entry state (for rollback purposes)."""
        if key not in self._layers:
            self._layers[key] = {}
        self._layers[key][entry.origin] = entry
        # Notify restoration if it becomes active
        active = self._get_active_entry(key)
        if active and active == entry:
            self._notify(key, entry.value, entry.origin)
        return True

    def reset_to_defaults(self) -> None:
        """
        Resets all configuration values to their SYSTEM or CONFIG defaults,
        clearing USER overrides.
        """
        keys = list(self._layers.keys())
        for key in keys:
            layers = self._layers[key]
            # Remove USER and GOD_MODE layers
            changed = False
            for origin in [OriginType.USER, OriginType.GOD_MODE]:
                if origin in layers:
                    del layers[origin]
                    changed = True

            if changed:
                active = self._get_active_entry(key)
                val = active.value if active else None
                origin = active.origin if active else OriginType.SYSTEM
                self._notify(key, val, origin)

    def migrate_from_dict(self, data: Dict[str, Any]) -> None:
        """
        Migrates a dictionary of configuration values into the registry.
        Assumes keys are 'domain.key' or simple keys.
        """
        for key, value in data.items():
            # Treat as SYSTEM origin if initial load, or CONFIG if manual migration?
            # Spec says "migrate_from_dict" for YAML/Config. So OriginType.CONFIG is appropriate.
            # But if it's the *initial* defaults, maybe SYSTEM?
            # Let's use CONFIG as it's safer (allows SYSTEM defaults to exist if we ever hardcode them).
            self.set(key, value, OriginType.CONFIG)
