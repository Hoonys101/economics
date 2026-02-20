File: modules\system\api.py
```python
from __future__ import annotations
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable, Union
from enum import IntEnum

# Existing imports from context
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

# ... (Previous existing definitions would be here, assuming incremental update or full file replacement. 
#      Since I cannot see the full file to append, I will provide the NEW interfaces and the RELEVANT existing ones needed for the spec.)

# --- Phase 1: Core Definitions (Preserved for Context) ---
CurrencyCode = str
DEFAULT_CURRENCY: CurrencyCode = "USD"
AgentID = int

class OriginType(IntEnum):
    SYSTEM = 0
    CONFIG = 10
    USER = 50
    GOD_MODE = 100

# --- Phase 1.2: Lifecycle & Dependency Hygiene Extensions ---

@runtime_checkable
class IAgentRegistry(Protocol):
    """
    Interface for the Agent Registry.
    Used by SettlementSystem to look up agents for transfers.
    """
    def get_agent(self, agent_id: Union[int, str]) -> Any:
        ...

    def get_all_financial_agents(self) -> List[Any]:
        ...

    def set_state(self, state: Any) -> None:
        ...

@runtime_checkable
class ISystemFactory(Protocol):
    """
    Factory interface for creating and wiring system components.
    Resolves TD-ARCH-DI-SETTLE by encapsulating dependency injection logic.
    """
    def create_settlement_system(self, bank: Any = None, metrics_service: Any = None) -> Any:
        """Creates the SettlementSystem."""
        ...

    def wire_dependencies(self, settlement_system: Any, agent_registry: IAgentRegistry) -> None:
        """Injects the AgentRegistry into the SettlementSystem."""
        ...

@runtime_checkable
class ILifecycleManager(Protocol):
    """
    Interface for managing the agent lifecycle (Death, Birth, Cleanup).
    """
    def execute_death_phase(self, state: Any) -> List[Any]:
        """
        Executes the death phase, returning any resulting transactions (e.g. inheritance).
        Must handle:
        1. Agent Liquidation
        2. Queue Scrubbing (TD-LIFECYCLE-STALE)
        3. Efficient State Cleanup (TD-SYS-PERF-DEATH)
        """
        ...
```

File: design\3_work_artifacts\specs\wave1-lifecycle-hygiene-spec.md
```markdown
# Spec: Wave 1 System Lifecycle & Dependency Hygiene

## 1. Overview
- **Goal**: Resolve critical technical debt in the System Lifecycle and Dependency Injection layers to ensure stability and performance.
- **Scope**: `SettlementSystem`, `DeathSystem`, `SimulationState`.
- **Key Features**:
    - Factory-based Dependency Injection for `SettlementSystem`.
    - O(1) Dictionary removal for Agent Death (vs O(N) rebuild).
    - `inter_tick_queue` scrubbing for dead agent transactions.

## 2. Technical Debt Resolution (The "Why")

| ID | Description | Resolution Strategy |
| :--- | :--- | :--- |
| **TD-ARCH-DI-SETTLE** | Temporal coupling in `SettlementSystem` (registry accessed before safe). | Implement `ISystemFactory` to enforce explicit wiring. Add `set_registry` to `SettlementSystem` interface. |
| **TD-SYS-PERF-DEATH** | O(N) `state.agents` rebuild in `DeathSystem`. | Refactor to targeted `del` operations on dictionaries. |
| **TD-LIFECYCLE-STALE** | Dead agent transactions linger in `inter_tick_queue`. | Implement `_scrub_queues` phase in `DeathSystem`. |

## 3. Detailed Design

### 3.1. Dependency Injection (SettlementSystem)

**Problem**: `SettlementSystem` depends on `IAgentRegistry` to resolve agent IDs during transfers. Currently, this dependency is implicit or lazily loaded, causing `RuntimeError` if accessed too early or in tests.

**Proposed Solution**:
1.  Define `ISettlementSystem` (or update `IMonetaryAuthority`) to include `set_registry(registry: IAgentRegistry)`.
2.  Use a `SystemFactory` pattern in `main.py` or `bootstrap.py` to:
    - Instantiate `SettlementSystem`.
    - Instantiate `AgentRegistry` (wrapping `SimulationState`).
    - Explicitly call `settlement_system.set_registry(agent_registry)`.
3.  **Strict Validation**: `SettlementSystem` methods requiring the registry (e.g., `transfer`, `get_balance`) must raise a clear `DependencyError` if called before `set_registry`.

**Pseudo-Code (SettlementSystem)**:
```python
class SettlementSystem(IMonetaryAuthority):
    def __init__(self, ...):
        self._registry: Optional[IAgentRegistry] = None

    def set_registry(self, registry: IAgentRegistry) -> None:
        self._registry = registry
        # Initialize internal engines that depend on registry immediately
        self._rebuild_engine()

    def _ensure_registry(self) -> IAgentRegistry:
        if not self._registry:
            raise DependencyError("SettlementSystem: Registry not injected via set_registry()")
        return self._registry
```

### 3.2. Lifecycle Optimization (DeathSystem)

**Problem**: `DeathSystem` clears and rebuilds the entire `state.agents` dictionary every tick if anyone dies. This is O(N) where N = Total Agents.

**Proposed Solution**:
1.  Identify dead agents.
2.  Perform targeted removal from `state.agents` (O(K) where K = Dead Agents).
3.  Perform list filtering on `state.households` and `state.firms` (O(N) but faster than dict rebuild).
4.  **Critical**: Scrub `inter_tick_queue` to remove "Zombie Transactions" (Transactions initiated by agents who just died).

**Pseudo-Code (DeathSystem)**:
```python
def execute(self, state: SimulationState) -> List[Transaction]:
    dead_agents: Set[AgentID] = set()
    
    # 1. Identify & Process (Liquidation)
    # ... logic to identify dead households/firms ...
    # ... logic to execute liquidation/inheritance ...
    
    # 2. Optimized Removal
    for agent_id in dead_agents:
        # O(1) Removal
        if agent_id in state.agents:
            del state.agents[agent_id]
        
        # O(1) Inactive Store
        if state.inactive_agents is not None:
            state.inactive_agents[agent_id] = agent  
            
    # 3. List Filtering (Necessary O(N) but minimized)
    state.households[:] = [h for h in state.households if h.id not in dead_agents]
    state.firms[:] = [f for f in state.firms if f.id not in dead_agents]
    
    # 4. Queue Scrubbing (TD-LIFECYCLE-STALE)
    self._scrub_queues(state, dead_agents)
    
    return transactions

def _scrub_queues(self, state: SimulationState, dead_ids: Set[AgentID]) -> None:
    # Filter out transactions where buyer OR seller is dead
    original_len = len(state.inter_tick_queue)
    state.inter_tick_queue[:] = [
        tx for tx in state.inter_tick_queue 
        if tx.buyer_id not in dead_ids and tx.seller_id not in dead_ids
    ]
    removed_count = original_len - len(state.inter_tick_queue)
    if removed_count > 0:
        self.logger.info(f"Scrubbed {removed_count} zombie transactions.")
```

## 4. Verification Plan

### 4.1. New Test Cases
- **Test Factory Wiring**: Verify `SystemFactory` correctly wires `AgentRegistry` into `SettlementSystem`.
- **Test Queue Scrubbing**: 
    1. Create a mock state with `inter_tick_queue` containing transactions from Agent A.
    2. Mark Agent A as dead.
    3. Run `DeathSystem`.
    4. Assert `inter_tick_queue` is empty.
- **Test Registry Guard**: Call `SettlementSystem.transfer` without `set_registry` and assert `DependencyError` (or strict logging error).

### 4.2. Regression Testing
- **Existing Tests**: All tests in `tests/` that instantiate `SettlementSystem` must be updated to either:
    - Inject a `Mock(spec=IAgentRegistry)`.
    - Or use the new `SystemFactory`.
- **Mock Update**: `conftest.py` likely needs an update to provide a pre-wired `SettlementSystem`.

## 5. Risk Assessment
- **Circular Imports**: `SettlementSystem` must NOT import `AgentRegistry` concrete class. It must only import `IAgentRegistry` Protocol.
- **Performance**: Queue scrubbing is O(M) where M is queue length. If M is massive, this adds overhead. However, typically M is small per tick.
- **Data Integrity**: Removing an agent from `state.agents` but failing to remove it from `state.households` would cause split-brain state. The `DeathSystem` logic must be atomic.

## 6. Mandatory Reporting
> **[Routine] Mandatory Reporting Instruction**: 
> Upon completion of the implementation, you must compile an insight report at `communications/insights/wave1-lifecycle-hygiene-spec.md`.
> This report must include:
> 1. Confirmation that `TD-ARCH-DI-SETTLE` is resolved via explicit injection.
> 2. Benchmark results (or logical proof) of O(1) removal vs O(N) rebuild.
> 3. List of any tests that required significant refactoring.
```