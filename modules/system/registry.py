from __future__ import annotations
from typing import Optional, Any, TYPE_CHECKING, Dict, List
from modules.system.api import IAgentRegistry, IGlobalRegistry, IConfigurationRegistry, OriginType, RegistryValueDTO, RegistryObserver, RegistryEntry, ISystemAgentRegistry, IAgent, AgentID
from modules.system.services.schema_loader import SchemaLoader
from simulation.dtos.registry_dtos import ParameterSchemaDTO
import threading
from contextlib import contextmanager

if TYPE_CHECKING:
    from simulation.agents import Agent
    from simulation.dtos.api import SimulationState

class AgentRegistry(IAgentRegistry, ISystemAgentRegistry):
    def __init__(self):
        # Migrated from WorldState
        self.agents: Dict[AgentID, Any] = {}
        self.households: List[Any] = []
        self.firms: List[Any] = []
        self._next_agent_id: int = 0
        self.inactive_agents: Dict[AgentID, Any] = {} # WO-109
        self._state = None # Keep for backward compat for now

    def set_state(self, state: Any) -> None:
        self._state = state

    def generate_next_agent_id(self) -> int:
        self._next_agent_id += 1
        return self._next_agent_id

    def register(self, agent: Any) -> None:
        """
        Registers an agent into the registry's state.
        Ensures atomic registration visibility.
        """
        self.agents[agent.id] = agent

        # Categorize
        if hasattr(agent, '__class__'):
            class_name = agent.__class__.__name__
            if 'Household' in class_name:
                self.households.append(agent)
            elif 'Firm' in class_name:
                self.firms.append(agent)

    def register_system_agent(self, agent: IAgent) -> None:
        """Registers a system agent bypassing standard initialization constraints."""
        self.agents[agent.id] = agent

    def get_system_agent(self, agent_id: AgentID) -> Optional[IAgent]:
        """Retrieves a system agent, supporting ID 0."""
        return self.agents.get(agent_id)

    def get_agent(self, agent_id: Any) -> Optional[Any]:
        if agent_id is None:
            return None

        agent = self.agents.get(agent_id)
        if agent is not None:
             return agent

        # Check Estate Registry (Fallback to legacy _state if available)
        if self._state and hasattr(self._state, 'estate_registry') and self._state.estate_registry:
             return self._state.estate_registry.get_agent(agent_id)

        return None

    def get_all_financial_agents(self) -> List[Any]:
        return list(self.agents.values())

    def get_all_agents(self) -> List[Any]:
        return list(self.agents.values())

    def get_all_households(self) -> List[Any]:
        return self.households

    def get_all_firms(self) -> List[Any]:
        return self.firms

    def is_agent_active(self, agent_id: int) -> bool:
        """Returns True if the agent exists and has not been marked INACTIVE/DEAD."""
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        return getattr(agent, "is_active", False)

    def purge_inactive(self) -> int:
        """Move inactive agents to inactive_agents dict. Returns purge count."""
        purged = 0
        inactive_ids = [aid for aid, agent in self.agents.items()
                       if hasattr(agent, 'is_active') and not agent.is_active]
        for aid in inactive_ids:
            self.inactive_agents[aid] = self.agents.pop(aid)
            purged += 1
        # Also remove from typed lists
        self.households = [h for h in self.households if getattr(h, 'is_active', True)]
        self.firms = [f for f in self.firms if getattr(f, 'is_active', True)]
        return purged

    def clear(self):
        """Full teardown for simulation finalization."""
        self.agents.clear()
        self.inactive_agents.clear()
        self.households.clear()
        self.firms.clear()


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
        # Source for current simulation tick (Callable[[], int] or object with .time/.current_tick)
        self._tick_source: Optional[Any] = None
        # Load metadata schema on initialization
        self._metadata_map: Dict[str, ParameterSchemaDTO] = {}
        self._metadata_loaded = False # Flag for lazy loading
        self._metadata_lock = threading.Lock() # Lock for thread-safe lazy loading
        self._batch_depth = 0
        self._batched_notifications: Dict[str, tuple[Any, OriginType]] = {}

        if initial_data:
            self.migrate_from_dict(initial_data)

    def _ensure_metadata_loaded(self) -> None:
        """
        Lazily loads metadata schema.
        Uses double-checked locking for thread safety.
        """
        if not self._metadata_loaded:
            with self._metadata_lock:
                if not self._metadata_loaded:
                    self._load_metadata()
                    self._metadata_loaded = True

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

    @contextmanager
    def batch_mode(self):
        """Defers notifications until the context block exits. Supports nesting."""
        if getattr(self, '_batch_depth', None) is None:
            self._batch_depth = 0
            self._batched_notifications = {}
        self._batch_depth += 1
        try:
            yield
        finally:
            self._batch_depth -= 1
            if self._batch_depth == 0:
                batched = self._batched_notifications
                self._batched_notifications = {}
                for key, (value, origin) in batched.items():
                    self._notify_immediate(key, value, origin)

    def get(self, key: str, default: Any = None) -> Any:
        # We don't necessarily need metadata to get a value, but consistent behavior is good.
        # However, metadata is mostly for validation/UI. Reading values should be fast.
        # Let's verify if metadata loading is required for GET.
        # Since SchemaLoader just reads a YAML file, it might be safer to lazy load it only when needed (e.g. get_metadata).
        # But if get() relies on defaults from schema (not implemented here), we'd need it.
        # Current impl doesn't use metadata in get(). So we can skip calling _ensure_metadata_loaded here for perf.
        entry = self._get_active_entry(key)
        return entry.value if entry else default

    def set(self, key: str, value: Any, origin: OriginType = OriginType.CONFIG) -> bool:
        # Metadata validation might happen here in future, but currently validation logic is in ConfigProxy.
        # So we can keep it light.
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

        # 2. Get Current Tick for Metadata
        current_tick = 0
        if self._tick_source:
             if callable(self._tick_source):
                 current_tick = self._tick_source()
             elif hasattr(self._tick_source, 'current_tick'):
                 current_tick = self._tick_source.current_tick
             elif hasattr(self._tick_source, 'time'):
                 current_tick = self._tick_source.time
             # Fallback to 0 if none of the above match
        
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
            last_updated_tick=current_tick
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
        if getattr(self, '_batch_depth', 0) > 0:
            self._batched_notifications[key] = (value, origin)
            return
        self._notify_immediate(key, value, origin)

    def _notify_immediate(self, key: str, value: Any, origin: OriginType) -> None:
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
        self._ensure_metadata_loaded() # Explicitly load metadata here
        return self._metadata_map.get(key)

    def get_entry(self, key: str) -> Optional[RegistryValueDTO]:
        return self._get_active_entry(key)

    def inject_tick_source(self, source: Any) -> None:
        """Injects the source for simulation time."""
        self._tick_source = source

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
