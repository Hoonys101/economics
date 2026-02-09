# Specification: PH11_THE_COCKPIT

## 1. Vision & Philosophy

"The Cockpit" transitions the Watchtower from a passive observation deck into an active control tower. It provides real-time "God-Mode" levers for policy experimentation while maintaining the critical macro-auditing functions of the original Watchtower. This hybrid model allows for direct interaction with the simulation's core parameters, enabling analysis of cause-and-effect in real-time.

The architecture explicitly addresses the risks identified in the pre-flight audit by separating read (monitoring) and write (control) operations into distinct, decoupled services to ensure system stability and testability.

## 2. System Architecture

To safely implement "Active Governance," the system will be split into two parallel data flows: a read-only **Observation Stream** and a write-only **Command Stream**.

### 2.1. High-Level Architectural Diagram

```
+-----------------+      (WebSocket: /ws/command)      +-----------------+      (Command Queue)      +--------------------+
| Frontend        |<----------------------------------- | CommandService  |-------------------------->| Simulation Engine  |
| (Next.js)       |       (Sends Control Commands)     | (Handles Writes)|      (Safe Processing)      | (Applies Changes)  |
|                 |                                    +-----------------+                           +--------------------+
|                 |                                                                                          |
|                 |       (WebSocket: /ws/live)                                                              | (State Update)
|                 |-----------------------------------> +-----------------+                                  |
|                 |   (Receives WatchtowerSnapshotDTO)   | DashboardService|<---------------------------------+
+-----------------+                                    | (Handles Reads) |      (Reads WorldState)
                                                         +-----------------+
```

### 2.2. Component Breakdown & Responsibilities

1.  **Frontend (Cockpit UI)**
    -   **Zone A (HUD)**: A fixed top bar displaying `tick`, `fps`, `m2_leak`, and `active_count` from the `WatchtowerSnapshotDTO`. It will house buttons that send `PAUSE`, `RESUME`, and `STEP` commands to the `/ws/command` endpoint.
    -   **Zone B (Policy Deck)**: A sidebar with control widgets (sliders, buttons). User interactions will generate specific command DTOs (e.g., `SetBaseRatePayload`) and send them to the `/ws/command` endpoint.
    -   **Zone C (Economic Monitor)**: The main view containing time-series charts and heatmaps populated by data from the `/ws/live` stream.

2.  **Backend Services (FastAPI)**
    -   **`DashboardService` (Read-Only)**: Its responsibility is unchanged. It continues to read the `simulation.world_state` at a throttled interval, package it into a `WatchtowerSnapshotDTO`, and stream it to the frontend via `/ws/live`. It will **not** handle any incoming commands.
    -   **`CommandService` (New Component, Write-Only)**: A new service responsible for handling all incoming "Active Governance" commands from the frontend via the `/ws/command` WebSocket. It validates incoming data against the command DTOs, and upon success, places the command onto a dedicated `command_queue` within the `Simulation` object. This decouples command reception from execution.
    -   **`SimulationEngine` (Modified)**: The core simulation loop (`tick()` method) will be modified. At the beginning of each tick, it will check the `command_queue` for pending commands. It will process all commands in the queue sequentially, applying changes to `SimulationConfig` or `WorldState` in a controlled, synchronous manner before proceeding with the tick's logic.

## 3. Detailed Design

### 3.1. API & DTO Definition (`modules/governance/cockpit/api.py`)

A new API file will be created to define the contracts for all control operations.

```python
# Path: modules/governance/cockpit/api.py
from typing import TypedDict, Literal, Union, Optional, Deque
from abc import ABC, abstractmethod
from dataclasses import dataclass

# --- Command Payloads ---

@dataclass
class SetBaseRatePayload:
    """Payload to set the central bank's base interest rate."""
    rate: float  # As a decimal, e.g., 0.05 for 5%

@dataclass
class TriggerHelicopterMoneyPayload:
    """Payload to distribute a flat amount of money to all households."""
    amount_per_capita: float

@dataclass
class SetWelfareBudgetPayload:
    """Payload to set the fraction of government revenue allocated to welfare."""
    welfare_budget_fraction: float

# --- Command DTO ---

@dataclass
class CockpitCommand:
    """The unified command structure sent from the frontend."""
    command_type: Literal[
        "SET_BASE_RATE",
        "TRIGGER_HELICOPTER_MONEY",
        "SET_WELFARE_BUDGET",
        "PAUSE_SIMULATION",
        "RESUME_SIMULATION",
        "STEP_SIMULATION"
    ]
    payload: Optional[Union[
        SetBaseRatePayload,
        TriggerHelicopterMoneyPayload,
        SetWelfareBudgetPayload,
    ]] = None

# --- Service Interface ---

class ICommandService(ABC):
    """Interface for the service that handles incoming cockpit commands."""
    @abstractmethod
    def __init__(self, command_queue: Deque[CockpitCommand]):
        ...

    @abstractmethod
    async def handle_command(self, raw_command: dict):
        """
        Parses, validates, and enqueues a command from the WebSocket.
        Raises ValueError on validation failure.
        """
        ...
```

### 3.2. Logic (Pseudo-code)

#### `CommandService` Implementation

```python
# from modules.governance.cockpit.api import ICommandService, CockpitCommand, ...

class CommandService(ICommandService):
    def __init__(self, command_queue):
        self.command_queue = command_queue

    async def handle_command(self, raw_command: dict):
        # 1. Validate raw_command structure
        if "command_type" not in raw_command:
            raise ValueError("Missing 'command_type'")

        command_type = raw_command["command_type"]
        payload_data = raw_command.get("payload")

        # 2. Create Payload DTO and validate data types/values
        payload_obj = None
        if command_type == "SET_BASE_RATE":
            payload_obj = SetBaseRatePayload(**payload_data)
            if not (0.0 <= payload_obj.rate <= 0.20):
                 raise ValueError("Base Rate must be between 0% and 20%")
        # ... other payload validations ...

        # 3. Create the final Command DTO
        command = CockpitCommand(command_type=command_type, payload=payload_obj)

        # 4. Enqueue the validated command for the engine
        self.command_queue.append(command)
        # Log the received command
```

#### `Simulation` Engine Modification

```python
# class Simulation:
    def __init__(self):
        # ... existing initializations
        self.command_queue: Deque[CockpitCommand] = collections.deque()
        self.is_paused = False

    def _process_commands(self):
        while self.command_queue:
            command = self.command_queue.popleft()
            # Apply command safely BEFORE the tick logic runs
            if command.command_type == "PAUSE_SIMULATION":
                self.is_paused = True
            elif command.command_type == "RESUME_SIMULATION":
                self.is_paused = False
            elif command.command_type == "SET_BASE_RATE":
                # This directly and safely modifies the config
                self.config.economy.base_interest_rate = command.payload.rate
                self.world_state.central_bank.base_rate = command.payload.rate
            # ... handle other commands ...

    def tick(self):
        self._process_commands()

        if self.is_paused:
            return # Skip the main tick logic

        # ... existing simulation tick logic ...
```

## 4. Verification Plan

-   **Unit Tests**:
    1.  `test_command_service_validation`: The `CommandService` correctly validates and rejects malformed payloads (e.g., out-of-bounds rate, incorrect data types).
    2.  `test_command_service_enqueues_valid_command`: A valid command sent to `CommandService` is correctly formatted and added to the mock `command_queue`.
    3.  `test_simulation_engine_processes_pause`: When a `PAUSE_SIMULATION` command is in the queue, the `simulation.tick()` method does not advance the world state time.
    4.  `test_simulation_engine_applies_config_change`: A `SET_BASE_RATE` command correctly updates the `simulation.config` value before the tick logic is executed.
-   **Integration Tests**:
    1.  A full client-server test where a WebSocket client sends a `SET_BASE_RATE` command. The test will assert that the subsequent `WatchtowerSnapshotDTO` received from `/ws/live` reflects the new rate.
-   **UX Pass/Fail Criteria**:
    1.  UI remains responsive (>30fps) while the simulation runs and commands are being sent.
    2.  Changing a slider value on the UI results in a confirmed state change in the simulation monitor within 2 seconds.

## 5. Risk & Impact Audit (Resolution)

This design directly mitigates the risks identified in the pre-flight audit:

-   **God Object Anti-Pattern (Resolved)**: The `CommandService` is introduced, separating write logic from the read/aggregation logic in `DashboardService`.
-   **Violation of SRP (Resolved)**: `DashboardService` is now only responsible for observation. `CommandService` is responsible for command validation and queuing. The `SimulationEngine` is responsible for command execution.
-   **State Mutation Risk (Resolved)**: The high-risk "hot-swap" requirement is implemented safely. The command queue and synchronous processing at the start of the `tick()` loop prevent race conditions and ensure that configuration changes are atomic and do not corrupt a mid-tick state.

## 6. Mandatory Reporting Verification

All insights, design decisions, and potential technical debt encountered during the implementation of The Cockpit (e.g., complexity of handling specific commands, performance bottlenecks) will be documented in `communications/insights/PH11_COCKPIT_IMPLEMENTATION.md`. This file will be created as part of the implementation task.
