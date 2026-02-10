# Spec: Cockpit Command Refactoring

## 1. Project Overview

-   **Goal**: Address technical debt `TD-255` by refactoring direct, synchronous state modifications from the manual "cockpit" into a traceable, asynchronous event-driven system.
-   **Scope**: This change targets manual intervention functions like setting tax rates or central bank interest rates. It introduces a new "System Command" processing pipeline.
-   **Key Features**:
    -   Introduction of `SystemCommand` DTOs for unilateral state changes.
    -   A new `SystemCommandProcessor` responsible for handling these commands.
    -   Integration into the `TickOrchestrator` via a new, dedicated phase to ensure architectural consistency.
    -   Enhanced auditability by logging the execution of every manual command.

## 2. System Architecture (High-Level)

The proposed architecture moves from a direct, synchronous call to an asynchronous, queued command pattern.

1.  **Command Generation**: The cockpit (e.g., `mission_active_cockpit`) no longer modifies `WorldState` directly. Instead, it instantiates a specific `SystemCommand` DTO (e.g., `SetTaxRateCommand`).
2.  **Command Queuing**: The generated DTO is appended to a new queue on the `WorldState` object: `world_state.system_command_queue`.
3.  **Command Injection**: At the start of each tick, the `TickOrchestrator` drains this queue and injects the commands into the `SimulationState` DTO for the current tick.
4.  **Command Processing**: A new phase, `Phase_SystemCommands`, is added to the `TickOrchestrator`'s sequence (executing early, after pre-sequence). This phase iterates through the commands in `SimulationState` and delegates their execution to a new `SystemCommandProcessor`.
5.  **Execution & Logging**: The `SystemCommandProcessor` interprets the command DTO, applies the state change to the `SimulationState`, and logs the action for audit purposes.

This design ensures that manual interventions are treated as first-class events within the simulation loop, respecting the single source of truth for state evolution and providing a clear audit trail.

## 3. Detailed Design

### 3.1. `modules/governance/api.py`

This file will define the data contracts (DTOs) and interfaces for the new system.

```python
from __future__ import annotations
from typing import TypedDict, Literal, Union
from enum import Enum

# --- Command Types ---

class SystemCommandType(Enum):
    """Defines the types of available system-level manual interventions."""
    SET_TAX_RATE = "SET_TAX_RATE"
    SET_INTEREST_RATE = "SET_INTEREST_RATE"
    # TBD (Team Leader Review Required): Other commands like SET_GOV_SPENDING_LEVEL etc.

# --- DTO Definitions ---

class BaseSystemCommand(TypedDict):
    """Base structure for all system commands."""
    command_type: SystemCommandType

class SetTaxRateCommand(BaseSystemCommand):
    """Command to set a specific tax rate for the government."""
    tax_type: str  # e.g., 'corporate', 'income'
    new_rate: float

class SetInterestRateCommand(BaseSystemCommand):
    """Command to set a specific interest rate for the central bank."""
    rate_type: str  # e.g., 'base_rate'
    new_rate: float

# --- Union Type for Handlers ---

SystemCommand = Union[
    SetTaxRateCommand,
    SetInterestRateCommand
]

# --- Processor Interface ---

class ISystemCommandHandler:
    """
    Interface for a processor that handles the execution of system commands.
    This will be implemented by the SystemCommandProcessor.
    """
    def execute(self, command: SystemCommand, state: 'SimulationState') -> 'SimulationState':
        """
        Executes a given command, modifying and returning the simulation state.

        Args:
            command: The command DTO to execute.
            state: The current simulation state DTO.

        Returns:
            The modified simulation state DTO.
        """
        ...
```

### 3.2. `simulation/dtos/api.py` (Modification)

The `SimulationState` DTO will be updated to include the list of commands for the current tick.

```python
# In simulation/dtos/api.py

from modules.governance.api import SystemCommand # Add this import

# ... existing SimulationState definition ...
class SimulationState(TypedDict):
    # ... other fields
    system_commands: List[SystemCommand] # Add this field
    # ... other fields
```

## 4. Logic & Implementation (Pseudo-code)

### 4.1. Cockpit (Command Generation)

```python
# In a cockpit/control script

from modules.governance.api import SystemCommandType, SetTaxRateCommand

# --- Old Synchronous Call (to be removed) ---
# world_state.government.tax_policy['corporate'] = 0.25

# --- New Asynchronous Command ---
def set_corporate_tax_rate(world_state: 'WorldState', new_rate: float):
    """Queues a command to change the corporate tax rate."""
    command = SetTaxRateCommand(
        command_type=SystemCommandType.SET_TAX_RATE,
        tax_type='corporate',
        new_rate=new_rate
    )
    world_state.system_command_queue.append(command)
    print(f"Command to set corporate tax to {new_rate} has been queued.")
```

### 4.2. TickOrchestrator (Injection & Phase Execution)

```python
# In simulation/orchestration/tick_orchestrator.py

# Add the new phase to imports
from simulation.orchestration.phases import Phase_SystemCommands # (New file)

class TickOrchestrator:
    def __init__(self, world_state: WorldState, action_processor: ActionProcessor):
        # ...
        self.phases: List[IPhaseStrategy] = [
            Phase0_PreSequence(world_state),
            Phase_SystemCommands(world_state), # <<< ADD NEW PHASE HERE
            Phase_Production(world_state),
            # ... rest of the phases
        ]
        # ...

    def _create_simulation_state_dto(self, ...) -> SimulationState:
        state = self.world_state

        # Drain the command queue from WorldState
        commands_for_tick = list(state.system_command_queue)
        state.system_command_queue.clear()

        return SimulationState(
            # ...
            system_commands=commands_for_tick, # Inject commands
            # ...
        )
```

### 4.3. Phase_SystemCommands (New Phase)

```python
# In simulation/orchestration/phases/system_commands.py (New file)

class Phase_SystemCommands(IPhaseStrategy):
    def __init__(self, world_state: 'WorldState'):
        # The processor would be instantiated and passed in, or get it from world_state
        self.system_command_processor = world_state.system_command_processor

    def execute(self, sim_state: SimulationState) -> SimulationState:
        if not sim_state.get('system_commands'):
            return sim_state

        for command in sim_state['system_commands']:
            sim_state = self.system_command_processor.execute(command, sim_state)

        sim_state['system_commands'].clear() # Clear after processing
        return sim_state
```

## 5. Verification & Test Plan

This refactoring has a **high impact** on the existing test suite due to the shift from synchronous to asynchronous state changes.

### 5.1. New Unit Tests

-   Create `tests/modules/governance/test_system_command_processor.py`.
-   Write specific tests for the `SystemCommandProcessor` for each `SystemCommandType`, ensuring it correctly modifies the state and logs its actions.
-   Use `golden_households` and `golden_firms` fixtures to create a realistic `SimulationState` for testing.

### 5.2. Test Migration Strategy

All tests relying on synchronous cockpit functions must be refactored.

**Example: Before Refactoring**

```python
def test_production_with_new_tax_rate(world_state):
    # 1. Synchronously set state
    world_state.government.tax_policy['corporate'] = 0.5

    # 2. Run logic
    some_firm = world_state.firms[0]
    some_firm.produce()

    # 3. Assert immediate outcome
    assert some_firm.expected_tax_payment == some_value
```

**Example: After Refactoring**

```python
def test_production_with_new_tax_rate(world_state, tick_orchestrator):
    # 1. Queue the command
    set_corporate_tax_rate(world_state, 0.5) # Helper that creates and queues the DTO

    # 2. Run the simulation for one tick to process the command
    tick_orchestrator.run_tick()

    # 3. Assert the state has been updated after the tick
    some_firm = world_state.firms[0]
    assert world_state.government.tax_policy['corporate'] == 0.5
    assert some_firm.expected_tax_payment == some_new_value
```

## 6. Risk & Impact Audit

This design explicitly addresses the risks identified in the pre-flight audit:

-   **God Class Dependencies**: By creating a dedicated `SystemCommandProcessor` and a new, distinct phase (`Phase_SystemCommands`), we avoid further polluting the legacy `ActionProcessor` and correctly integrate into the `TickOrchestrator`'s lifecycle.
-   **Semantic Mismatch**: The new `SystemCommand` DTOs provide a clear, semantically appropriate data structure for unilateral commands, avoiding the anti-pattern of forcing them into the `Transaction` model.
-   **Orchestration Integrity**: The asynchronous, queue-based architecture ensures all manual interventions are processed within the `TickOrchestrator`'s phased execution, preserving state consistency and resolving the core issue of `TD-255`.
-   **High Risk to Tests**: We acknowledge this is a **major breaking change** for the test suite. A significant, dedicated effort will be required to migrate tests to the asynchronous pattern. This is a necessary cost to pay for correcting the fundamental architectural flaw.

## 7. Mandatory Reporting Verification

-   An insight report has been generated to document this design decision and its consequences.
-   **File**: `communications/insights/TD-255_Cockpit_Event_Refactoring.md`
-   **Content**: This report details the choice to implement a separate command processing pipeline rather than overloading the transaction system, justifies the new architecture, and highlights the unavoidable impact on the test suite, providing a migration strategy.
