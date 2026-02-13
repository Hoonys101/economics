from __future__ import annotations
from typing import Optional, Any, TYPE_CHECKING, Dict, List
from modules.system.api import IAgentRegistry, IGlobalRegistry, OriginType, RegistryEntry, RegistryObserver

if TYPE_CHECKING:
    from simulation.agents import Agent
    from simulation.dtos.api import SimulationState

class AgentRegistry(IAgentRegistry):
    def __init__(self):
        self._state: Optional[SimulationState] = None

    def set_state(self, state: SimulationState) -> None:
        self._state = state

    def get_agent(self, agent_id: Any) -> Optional[Agent]:
        if self._state is None:
            return None

        agent = self._state.agents.get(agent_id)
        if agent:
            return agent

        # Fallback for government if not in agents map
        if hasattr(self._state, 'government') and self._state.government:
            if agent_id == "government" or agent_id == self._state.government.id:
                return self._state.government

        return None

    def get_all_financial_agents(self) -> List[Any]:
        if self._state is None:
            return []

        # Start with all registered agents
        all_agents = list(self._state.agents.values())

        # Ensure Government, Bank, Central Bank are included if not already
        known_ids = {a.id for a in all_agents if hasattr(a, 'id')}

        extras = [self._state.government, self._state.bank, self._state.central_bank]
        for extra in extras:
            if extra and hasattr(extra, 'id') and extra.id not in known_ids:
                all_agents.append(extra)
                known_ids.add(extra.id)

        return all_agents

class GlobalRegistry(IGlobalRegistry):
    """
    Central repository for simulation parameters with priority and locking mechanisms.
    FOUND-01: Implements Origin-based access control and observer pattern.
    """
    def __init__(self):
        self._storage: Dict[str, RegistryEntry] = {}
        self._observers: List[RegistryObserver] = []
        self._key_observers: Dict[str, List[RegistryObserver]] = {}
        # Placeholder for scheduler injection (Phase 0 Intercept)
        self._scheduler = None

    def get(self, key: str, default: Any = None) -> Any:
        entry = self._storage.get(key)
        return entry.value if entry else default

    def set(self, key: str, value: Any, origin: OriginType = OriginType.CONFIG) -> bool:
        current_entry = self._storage.get(key)

        # 1. Authority Check
        if current_entry:
            # If locked, only GOD_MODE (or equivalent high privilege) can modify
            if current_entry.is_locked:
                if origin < OriginType.GOD_MODE:
                     raise PermissionError(f"Target '{key}' is locked by {current_entry.origin.name}")

            # Priority Check: Lower priority cannot overwrite higher priority
            if origin < current_entry.origin:
                return False

        # 2. Phase 0 Intercept (TODO: Implement when Scheduler is available)
        # if self._scheduler and not self._scheduler.is_in_phase_0():
        #     self._pending_updates.append((key, value, origin))
        #     return False

        # 3. Update
        # If origin is GOD_MODE, we implicitly lock it unless explicitly managed?
        # Spec says "is_locked=(origin == OriginType.GOD_MODE)"
        is_locked = (origin == OriginType.GOD_MODE)

        # If currently locked and we are GOD_MODE, preserve lock unless unlock() called?
        # If GOD_MODE calls set(), it sets is_locked=True.
        # This aligns with "Force Lock" concept for God Mode intervention.

        new_entry = RegistryEntry(
            value=value,
            origin=origin,
            is_locked=is_locked,
            last_updated_tick=0 # TODO: Inject scheduler.current_tick
        )
        self._storage[key] = new_entry
        self._notify(key, value, origin)
        return True

    def lock(self, key: str) -> None:
        """Locks a specific parameter with God-Mode authority."""
        entry = self._storage.get(key)
        if entry:
            self._storage[key] = RegistryEntry(
                value=entry.value,
                origin=OriginType.GOD_MODE, # Escalates origin to GOD_MODE
                is_locked=True,
                last_updated_tick=entry.last_updated_tick
            )

    def unlock(self, key: str) -> None:
        """Unlocks a parameter, allowing updates from equal or higher origin."""
        entry = self._storage.get(key)
        if entry:
             self._storage[key] = RegistryEntry(
                 value=entry.value,
                 origin=entry.origin, # Keep origin (likely GOD_MODE from lock)
                 is_locked=False,
                 last_updated_tick=entry.last_updated_tick
             )

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

    def snapshot(self) -> Dict[str, RegistryEntry]:
        return self._storage.copy()
