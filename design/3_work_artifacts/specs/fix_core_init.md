modules/system/services/api.py
```python
from __future__ import annotations
from typing import List, Protocol, Any, runtime_checkable
from dataclasses import dataclass

from simulation.dtos.commands import GodCommandDTO

@dataclass
class CommandResultDTO:
    command_id: str
    success: bool
    failure_reason: str = ""
    affected_entities: List[str] = None

@runtime_checkable
class ICommandService(Protocol):
    """
    Interface for the CommandService responsible for executing batches of GodCommands.
    """
    def execute_command_batch(
        self, 
        commands: List[GodCommandDTO], 
        tick: int, 
        baseline_m2: float
    ) -> List[CommandResultDTO]:
        """
        Executes a batch of commands and returns their results.
        
        Args:
            commands: List of GodCommandDTOs to execute.
            tick: Current simulation tick.
            baseline_m2: Current baseline money supply for validation.
            
        Returns:
            List of CommandResultDTO indicating success/failure of each command.
        """
        ...

```

design/3_work_artifacts/specs/core_init_fix_spec.md
```markdown
# Specification: Core Simulation Initialization & Command Processing Fix

## 1. Overview
This specification addresses critical regression failures in the `Simulation` engine startup sequence. Specifically, it resolves a signature mismatch in `Simulation.__init__` by correctly injecting `CommandService` via `SimulationInitializer`, and fixes a `NameError` in the `_process_commands` method.

## 2. Scope
- **Target Files**:
  - `simulation/engine.py`
  - `simulation/initialization/initializer.py`
  - `tests/conftest.py` (or relevant test setups)
- **Goal**: Restore green state for core initialization tests (`test_simulation_initialization`, etc.).

## 3. Detailed Changes

### 3.1. `simulation/engine.py`

#### Logic Fix: `_process_commands`
The variable `commands` is used before initialization. It must be explicitly initialized to an empty list before any accumulation logic.

```python
# Pseudo-code for _process_commands
def _process_commands(self) -> None:
    # FIX: Initialize container explicitly
    commands: List[GodCommandDTO] = []

    # 1. Drain External Queue
    if hasattr(self.world_state, "command_queue"):
        # ... fetch from command_queue and append to commands ...
    
    # 2. Drain Internal God Queue
    # ... fetch from god_command_queue and append to commands ...

    if not commands:
        return

    # ... execution logic ...
```

### 3.2. `simulation/initialization/initializer.py`

#### Dependency Injection: `build_simulation`
The `Simulation` constructor now requires `command_service`. We must instantiate `CommandService` and inject it.

**Architectural Consideration**:
If `CommandService` requires `WorldState` to function, we face a circular dependency (`Simulation` creates `WorldState`).
*Strategy*: Instantiate `CommandService` with `GlobalRegistry` (which is available). If `CommandService` requires `WorldState`, it should be injected via a setter *after* `Simulation` (and `WorldState`) creation, or passed dynamically during method calls.
*Assumption*: For this fix, we assume `CommandService` can be instantiated with `ConfigManager` or similar available dependencies, or we use `GlobalRegistry` to resolve `WorldState` later.

```python
# Pseudo-code for build_simulation
def build_simulation(self) -> Simulation:
    # ... Lock acquisition ...
    
    # 1. Pre-instantiate Core Systems
    global_registry = GlobalRegistry()
    settlement_system = SettlementSystem(logger=self.logger)
    agent_registry = AgentRegistry()
    
    # 2. Instantiate CommandService (NEW)
    # Ensure all required deps for CommandService are present
    from modules.system.services.command_service import CommandService
    command_service = CommandService(
        config_manager=self.config_manager,
        registry=global_registry # Passing registry allows late binding of WorldState
    )

    # 3. Create Simulation Shell
    sim = Simulation(
        config_manager=self.config_manager,
        config_module=self.config,
        logger=self.logger,
        repository=self.repository,
        registry=global_registry,
        settlement_system=settlement_system,
        agent_registry=agent_registry,
        command_service=command_service # INJECTED
    )
    
    # ... Post-instantiation wiring ...
    
    return sim
```

## 4. Verification & Testing Strategy

### 4.1. Unit Test Updates (`tests/`)
Many tests manually instantiate `Simulation`. These must be updated to mock `CommandService`.

**`tests/unit/test_tax_incidence.py` (and others):**
```python
# Pseudo-code for test setup update
@pytest.fixture
def mock_command_service():
    service = MagicMock(spec=CommandService)
    service.execute_command_batch.return_value = []
    return service

def test_simulation_init(mock_config, mock_logger, mock_repo, mock_registry, mock_settlement, mock_agent_registry, mock_command_service):
    sim = Simulation(
        ...,
        command_service=mock_command_service
    )
    assert sim is not None
```

### 4.2. Acceptance Criteria
1.  `_process_commands` does not raise `NameError` when queues are empty or full.
2.  `SimulationInitializer.build_simulation()` completes without `TypeError`.
3.  Existing tests in `tests/integration/test_wo058_production.py` pass.

## 5. Risk Assessment (Audit)
-   **Circular Dependency**: If `CommandService` strictly requires `WorldState` in its `__init__`, this refactor will fail. *Mitigation*: Verify `CommandService` implementation. If it needs `WorldState`, change `Simulation` to accept `Optional[CommandService]` (not recommended) or use a `WorldStateProvider`.
-   **Test Cascade**: There are likely many more tests than identified in the log that manually instantiate `Simulation`. A global search for `Simulation(` is recommended to catch all call sites.

## 6. Mandatory Reporting
**Jules (User)** must perform the following reporting task:
1.  Create `communications/insights/spec-fix-core-init.md`.
2.  Document the dependency injection approach used for `CommandService`.
3.  Run `pytest tests/integration/test_wo058_production.py` and paste the output into the report.
```