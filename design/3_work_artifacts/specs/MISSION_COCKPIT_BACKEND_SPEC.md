file: modules/core/global_registry.py
```python
from __future__ import annotations
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable, Union
from dataclasses import dataclass
from enum import IntEnum

# ==============================================================================
# 1. Enums & Types
# ==============================================================================

class OriginType(IntEnum):
    """
    Priority Level for Parameter Updates.
    Higher value = Higher Priority.
    """
    SYSTEM = 0          # Hardcoded defaults
    CONFIG = 10         # Loaded from file (User Configuration)
    USER = 50           # Dashboard/UI manual override
    GOD_MODE = 100      # Absolute override (Scenario Injection)

@dataclass
class RegistryEntry:
    value: Any
    origin: OriginType
    is_locked: bool = False
    last_updated_tick: int = 0

# ==============================================================================
# 2. Interfaces
# ==============================================================================

class RegistryObserver(Protocol):
    def on_registry_update(self, key: str, value: Any, origin: OriginType) -> None:
        """
        Callback triggered when a subscribed key is updated.
        """
        ...

@runtime_checkable
class IGlobalRegistry(Protocol):
    """
    Interface for the Global Parameter Registry (SSoT).
    Resolves TD-CONF-GHOST-BIND by allowing runtime parameter resolution.
    """

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a configuration value.
        Must always fetch the current value (no caching in consumer).
        """
        ...

    def set(self, key: str, value: Any, origin: OriginType = OriginType.USER) -> bool:
        """
        Updates a configuration value if the origin has sufficient priority.
        Returns True if the update was applied.
        """
        ...

    def lock(self, key: str) -> bool:
        """
        Locks a key to prevent further modification until unlocked.
        Returns True if lock was successful.
        """
        ...

    def unlock(self, key: str) -> bool:
        """
        Unlocks a key.
        """
        ...

    def subscribe(self, observer: RegistryObserver, keys: Optional[List[str]] = None) -> None:
        """
        Registers an observer to be notified of updates.
        If keys is None, subscribes to all updates.
        """
        ...

    def snapshot(self) -> Dict[str, RegistryEntry]:
        """
        Returns a complete snapshot of the current state for serialization/debugging.
        """
        ...

    def reset_to_defaults(self) -> None:
        """
        Resets all values to their CONFIG/SYSTEM state, clearing USER/GOD_MODE overrides.
        """
        ...

# ==============================================================================
# 3. Global Singleton Accessor (Draft)
# ==============================================================================

_registry_instance: Optional[IGlobalRegistry] = None

def get_registry() -> IGlobalRegistry:
    """
    Accessor for the singleton registry instance.
    Raises RuntimeError if not initialized.
    """
    global _registry_instance
    if _registry_instance is None:
        # In a real implementation, this might lazy-load or raise
        raise RuntimeError("GlobalRegistry not initialized. Call initialize_registry() first.")
    return _registry_instance

def initialize_registry(implementation: IGlobalRegistry) -> None:
    """
    Sets the global registry implementation.
    """
    global _registry_instance
    _registry_instance = implementation
```

file: modules/watchtower/models/genealogy.py
```python
from __future__ import annotations
from typing import List, Optional, Dict, Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

# ==============================================================================
# 1. Pydantic Models (Contract Compliance)
# ==============================================================================

class AgentSurvivalData(BaseModel):
    """
    Immutable record of an agent's life cycle.
    Used for 'Nature vs Nurture' analysis (Genealogy Plot).
    """
    agent_id: int
    agent_type: str = Field(..., description="HOUSEHOLD or FIRM")
    generation: int
    birth_tick: int
    death_tick: Optional[int] = None
    peak_wealth: int = Field(default=0, description="Max wealth achieved in Pennies")
    cause_of_death: Optional[str] = None
    
    # Genetic/Initial Traits (Nature)
    initial_risk_tolerance: float
    initial_ambition: float
    initial_social_class: str # "LOWER", "MIDDLE", "UPPER" based on starting assets
    
    # Outcomes (Nurture/Fate)
    lifetime_earnings: int = 0
    reproduction_count: int = 0

class GenealogyResponse(BaseModel):
    """
    API Response for the Genealogy endpoint.
    """
    dataset: List[AgentSurvivalData]
    total_records: int
    filter_metadata: Dict[str, Any]

# ==============================================================================
# 2. Repository Interface
# ==============================================================================

@runtime_checkable
class IGenealogyRepository(Protocol):
    """
    Interface for archiving and retrieving agent life history.
    """

    def archive_agent(self, data: AgentSurvivalData) -> None:
        """
        Persists a single agent's record. 
        Should be non-blocking or efficient (e.g., append to buffer/SQLite).
        """
        ...

    def get_records(
        self, 
        limit: int = 1000, 
        min_generation: int = 0,
        agent_type: Optional[str] = None
    ) -> List[AgentSurvivalData]:
        """
        Retrieves records matching filters.
        """
        ...
    
    def get_agent_record(self, agent_id: int) -> Optional[AgentSurvivalData]:
        """
        Retrieves a specific agent's record.
        """
        ...
```

file: design/3_work_artifacts/specs/spec-cockpit-backend.md
```markdown
# Spec: Cockpit 2.0 Backend Implementation

## 1. Introduction
This specification details the implementation of the backend services required to support Cockpit 2.0. It encompasses the migration of telemetry to Pydantic, the establishment of a Global Configuration Registry, and the creation of an Agent Genealogy system.

**Primary Objectives:**
- **Type Safety**: Enforce strict contracts between Backend and Frontend via Pydantic.
- **Dynamic Configuration**: Enable runtime parameter tuning via `GlobalRegistry`.
- **Long-term Analysis**: Enable "Nature vs Nurture" analysis via `GenealogyRepository`.

## 2. Architecture & Components

### 2.1. Pydantic Migration (`simulation/dtos/watchtower.py`)
The existing `dataclass` based `WatchtowerSnapshotDTO` will be replaced by `pydantic.BaseModel` definitions that strictly mirror the `MISSION_COCKPIT_API_CONTRACT.md`.

- **Strategy**: 
  - `simulation/dtos/watchtower.py` will import the authoritative models from `modules/governance/cockpit/api.py`.
  - It will re-export them to maintain backward compatibility for imports where possible, OR `DashboardService` will be updated to import directly from `modules/governance/cockpit/api.py`.
  - **Decision**: `DashboardService` will import directly from `modules/governance/cockpit/api.py` to ensure SSoT. `simulation/dtos/watchtower.py` will be marked deprecated or refactored to alias the new models.

### 2.2. Global Registry (`modules/core/global_registry.py`)
A Singleton implementation of `IGlobalRegistry`.

- **Storage**: `Dict[str, RegistryEntry]`
- **Initialization**: 
  - On startup (`server.py`), it loads values from `config.py`.
  - It recursively traverses `config` modules/dicts to flatten keys (e.g., `finance.base_rate`).
- **Integration**:
  - `server.py` initializes the registry.
  - `SetParamCommand` handler in `server.py` calls `registry.set()`.
  - **Phase 2 (Future)**: Core Engines will be refactored to call `registry.get()` instead of using module-level constants.

### 2.3. Agent Genealogy (`modules/watchtower/models/genealogy.py`)
A repository system to track agent lifecycles.

- **Model**: `AgentSurvivalData` (Immutable Pydantic Model).
- **Storage**: `SQLite` (via `sqlite3` built-in) or In-Memory List (for MVP).
  - **Decision**: In-Memory List with CSV Dump on Shutdown for MVP to avoid strict DB dependency in this phase.
- **Hook**:
  - `DeathSystem` will receive an optional `IGenealogyRepository`.
  - When an agent is liquidated, `DeathSystem` calls `repo.archive_agent()`.

### 2.4. Dashboard Service Hardening (`simulation/orchestration/dashboard_service.py`)
- **Refactor**:
  - Remove `asdict` calls.
  - Construct `WatchtowerSnapshotResponse` (Pydantic) directly.
  - Use `model.model_dump(mode='json')` for serialization.

## 3. Implementation Details

### 3.1. `simulation/orchestration/dashboard_service.py` Logic
```python
# Pseudo-code update
from modules.governance.cockpit.api import WatchtowerSnapshotResponse, IntegrityMetrics, ...

class DashboardService:
    def get_snapshot(self) -> WatchtowerSnapshotResponse:
        # ... calculation logic ...
        return WatchtowerSnapshotResponse(
            timestamp=datetime.now().timestamp(),
            integrity=IntegrityMetrics(m2_leak=..., fps=...),
            # ... nested models ...
        )
```

### 3.2. `server.py` API Endpoints

#### WebSocket `/ws/command`
```python
# Pseudo-code
from modules.governance.cockpit.api import CockpitCommand
from pydantic import TypeAdapter

adapter = TypeAdapter(CockpitCommand)

@app.websocket("/ws/command")
async def command_endpoint(websocket: WebSocket):
    # ...
    try:
        payload = await websocket.receive_json()
        command = adapter.validate_python(payload) # Strict validation
        
        if command.type == "SET_PARAM":
            registry.set(command.param_key, command.value, origin=OriginType.GOD_MODE)
        # ... handle other types ...
    except ValidationError as e:
        logger.error(f"Invalid Command: {e}")
```

#### REST `/api/v1/inspector/{agent_id}`
```python
@app.get("/api/v1/inspector/{agent_id}", response_model=AgentInspectorResponse)
def get_agent_inspector(agent_id: int):
    agent = sim.world_state.agents.get(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    
    # Map internal agent state to AgentInspectorResponse
    return AgentInspectorResponse(...)
```

### 3.3. `DeathSystem` Hook
```python
class DeathSystem:
    def __init__(self, ..., genealogy_repo: Optional[IGenealogyRepository] = None):
        self.genealogy_repo = genealogy_repo

    def _handle_agent_liquidation(self, state):
        # ... existing logic ...
        for household in inactive_households:
             if self.genealogy_repo:
                 data = AgentSurvivalData(
                     agent_id=household.id,
                     agent_type="HOUSEHOLD",
                     birth_tick=household.bio_state.birth_tick, # Assuming availability
                     death_tick=state.time,
                     peak_wealth=household.historical_peak_wealth, # Needs adding to EconState
                     cause_of_death="STARVATION" # Heuristic
                 )
                 self.genealogy_repo.archive_agent(data)
```

## 4. Verification Plan

### 4.1. Automated Tests
- **Pydantic Validation**: Create `tests/unit/test_cockpit_models.py` to verify strict validation of JSON payloads.
- **Registry Behavior**: Create `tests/unit/test_global_registry.py` to verify locking, origin priority, and observer callbacks.
- **Serialization**: Verify `DashboardService.get_snapshot().model_dump()` produces valid JSON matching the contract.

### 4.2. Manual Verification
- **WS Connection**: Connect via Postman/wscat to `/ws/live` and verify JSON structure.
- **God Mode**: Send `SET_PARAM` command and verify `registry.get()` reflects the change.

## 5. Technical Debt Analysis
- **Resolves**:
  - `TD-UI-DTO-PURITY`: Full Pydantic adoption.
  - `TD-CONF-GHOST-BIND`: Registry infrastructure established.
- **New Debt**:
  - **TD-GENEALOGY-MVP**: In-memory storage for genealogy is temporary. Needs real DB.
  - **TD-DASHBOARD-CONVERSION**: `DashboardService` mapping logic is becoming a monolithic mapper. Should be split into sub-mappers (e.g., `MacroMapper`, `FinanceMapper`).

```

file: communications/insights/spec-cockpit-backend.md
```markdown
# Insight Report: Cockpit 2.0 Backend Spec

## 1. Architectural Insights
- **Contract Primacy**: The decision to import Pydantic models directly from `modules/governance/cockpit/api.py` into `DashboardService` effectively treats the Governance module as the defining contract for the API. This inverts the typical dependency where the API reflects the internal model, enforcing a "Schema-First" approach.
- **Registry Injection**: Introducing `GlobalRegistry` requires a careful boot sequence in `server.py`. The registry must be seeded *before* the simulation loop starts. This is a critical initialization phase that was previously implicit in module imports.

## 2. Technical Debt Addressal
- **TD-UI-DTO-PURITY**: The move to Pydantic `BaseModel` allows for `model_dump(mode='json')`, which handles nested serialization automatically, removing the fragile manual `asdict` logic in `server.py`.
- **TD-CONF-GHOST-BIND**: While `GlobalRegistry` provides the *mechanism* for dynamic config, existing modules still import constants (e.g., `from config import MIN_WAGE`). These modules will **not** react to registry changes until they are refactored to use `registry.get("MIN_WAGE")`. This spec only implements the infrastructure (Phase 1).

## 3. Risks & Mitigation
- **Performance**: Pydantic V2 is fast (Rust-based), but creating complex nested models at 1Hz for a large snapshot might have overhead.
  - *Mitigation*: Benchmark `get_snapshot` execution time. If >50ms, consider caching parts of the snapshot (e.g., Population Distribution) that change slowly.
- **Synchronization**: The `GenealogyRepository` hook in `DeathSystem` adds a synchronous write operation (even if in-memory).
  - *Mitigation*: Ensure the repository implementation is extremely lightweight (O(1) append).
```