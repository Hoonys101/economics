# Mission Insight Report: Active Control Cockpit

**Mission Key:** `mission_active_cockpit`
**Date:** 2024-05-22
**Author:** Jules

## 1. Problem Phenomenon
The simulation was previously a "fire-and-forget" system. Once started, it ran according to its initial configuration and internal logic without any means for external intervention.
- **Symptom**: Users could observe the simulation via `watchtower` but could not pause, resume, step through ticks for debugging, or adjust parameters like interest rates dynamically to test hypotheses.
- **Impact**: Reduced observability and debuggability. Inability to perform "human-in-the-loop" experiments.

## 2. Root Cause Analysis
- **Architecture**: The `Simulation` class encapsulated the run loop (`run_tick`) and state (`WorldState`) without exposing an interface for runtime command injection.
- **Communication**: The WebSocket server (`server.py`) was unidirectional (server-to-client) for the dashboard, lacking a channel for client-to-server commands.
- **Concurrency**: The simulation runs in a separate thread/process from the API server, requiring a thread-safe mechanism to pass commands.

## 3. Solution Implementation Details
The solution implements a **Command Pattern** with a **WebSocket Command Stream**.

### 3.1. Command DTOs (`modules/governance/cockpit/api.py`)
Defined strict DTOs for commands to ensure type safety and validation.
- `CockpitCommand`: Wrapper with `type` and `payload`.
- `CockpitCommandType`: Enum-like literal (`PAUSE`, `RESUME`, `STEP`, `SET_BASE_RATE`, `SET_TAX_RATE`).

### 3.2. Command Service (`simulation/orchestration/command_service.py`)
A thread-safe service using `collections.deque` to buffer commands.
- Validates payloads (e.g., rate limits).
- Acts as the bridge between the async FastAPI server and the sync Simulation loop.

### 3.3. Engine Modification (`simulation/engine.py`)
Intercepted the `run_tick` method.
- **Pre-Tick Processing**: Before delegating to `TickOrchestrator`, the engine processes all pending commands.
- **Control Flow**: Implemented `is_paused` and `step_requested` flags to control the execution loop.
- **State Injection**: Directly modifies `WorldState` components (e.g., `central_bank.base_rate`) based on commands.

### 3.4. Frontend (`watchtower/`)
Enhanced the Next.js dashboard.
- **Dual WebSocket**: Maintains a separate WebSocket connection for commands (`/ws/command`) to keep the high-frequency telemetry stream (`/ws/live`) clean.
- **UI Controls**: Added Play/Pause/Step buttons and a Base Rate slider.

## 4. Lessons Learned & Technical Debt

### Lessons Learned
- **Facade Pattern**: The `Simulation` class acting as a facade made it easy to inject the command processing logic without touching the complex internal orchestration logic.
- **Thread Safety**: Using `deque` is sufficient for this single-producer (Server), single-consumer (Simulation) model in CPython due to the GIL and atomic operations, but explicit locking might be safer for future multi-threaded expansions.

### Technical Debt Identified
- **Direct State Modification**: The `SET_BASE_RATE` command directly modifies `central_bank.base_rate`. Ideally, this should be routed through a "Divine Intervention" event or a specific policy override mechanism to ensure consistent logging and side effects (e.g., triggering a "Rate Change" event for agents to react to immediately).
- **Tax Rate Logic**: `SET_TAX_RATE` modifies `government.corporate_tax_rate` directly. However, the Government agent has complex internal logic (`FiscalPolicyDTO`, legacy `tax_service` logic) which might overwrite this value in the next tick if `ENABLE_FISCAL_STABILIZER` is active. This interaction needs further verification.
- **Frontend State Sync**: The frontend slider does not automatically sync with the simulation's actual rate if the simulation changes it internally (e.g., via Taylor Rule). It is currently a "write-only" control in terms of UI feedback loop.

## 5. Verification
- **Unit Tests**: `tests/unit/orchestration/test_command_service.py` verified validation and queue logic.
- **Manual Verification**: Confirmed that `PAUSE` stops the tick counter, and `RESUME` continues it. Verified `SET_BASE_RATE` updates the value in the backend.
