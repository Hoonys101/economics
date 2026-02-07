# Technical Insight Report: TD-268 BaseAgent Initialization Refactor

## 1. Problem Phenomenon
The initialization logic for `BaseAgent` and its subclasses (`Household`, `Firm`) was tightly coupled and inflexible.
- **Monolithic `BaseAgentInitDTO`**: It combined configuration (ID, name), state (assets, needs), and dependencies (decision engine) into a single object.
- **Constructor Overload**: Subclasses like `Household` and `Firm` had massive constructors taking many arguments, then constructing `BaseAgentInitDTO` to pass to `super().__init__`.
- **Mixing Concerns**: Immutable identity and mutable state were mixed during initialization, making it hard to support "loading from state" (hydration) or clean dependency injection.

## 2. Root Cause Analysis
The original design used `BaseAgentInitDTO` as a "catch-all" parameter object pattern. While better than raw arguments, it became a God Object for initialization.
- **Violation of Orchestrator-Engine**: The Agent (Orchestrator) was not clearly separated from its State and Engine during construction.
- **Testing Difficulty**: Setting up an agent required constructing complex DTOs even for simple tests.

## 3. Solution Implementation Details
We refactored the initialization process into a 2-stage protocol: **Instantiation** and **Hydration**.

### 3.1. New DTOs and Interfaces (`modules/simulation/api.py`)
- **`AgentCoreConfigDTO`**: Immutable core configuration (ID, Name, Value Orientation, Initial Needs, Logger).
- **`AgentStateDTO`**: Mutable state snapshot (Assets, Inventory, Active Status).
- **`IDecisionEngine`**: Interface for decision logic.
- **`IOrchestratorAgent`**: Interface defining the new protocol (`load_state`, `get_core_config`, etc.).

### 3.2. Refactored `BaseAgent` (`simulation/base_agent.py`)
- Constructor now accepts only `core_config` and `engine`.
- Implements `load_state(state: AgentStateDTO)` to populate `_wallet` and `_inventory`.
- Removed `BaseAgentInitDTO`.

### 3.3. Refactored Subclasses
- **`Household`** (`simulation/core_agents.py`):
    - Constructor updated to accept `core_config` and `engine`.
    - `_econ_state` initialization updated to use `BaseAgent`'s wallet and inventory instances.
- **`Firm`** (`simulation/firms.py`):
    - Constructor updated. Removed `initial_capital` logic from constructor (now handled via `load_state` or Genesis).
    - `clone` method updated to support new flow.

### 3.4. Updated Simulation Builder (`utils/simulation_builder.py`)
- Refactored `create_simulation` to:
    1. Create `AgentCoreConfigDTO`.
    2. Instantiate Agent.
    3. Create initial `AgentStateDTO` (with 0 assets).
    4. Call `load_state`.

## 4. Lessons Learned & Technical Debt
- **Breaking Changes**: This refactor broke all existing tests and scripts that instantiated agents directly. We fixed `tests/unit/test_base_agent.py` and `utils/simulation_builder.py`, but many verification scripts in `scripts/` are likely broken and need updates.
- **Inventory Alias Risk**: `Household` aliases `BaseAgent._inventory` in `_econ_state`. `BaseAgent.load_state` must carefully update the dictionary content (`clear()` + `update()`) rather than replacing the object reference, to maintain consistency. We implemented this safe pattern.
- **Government Agent**: `Government` does not inherit from `BaseAgent` and was not refactored. It implements `IAgent` but not `IOrchestratorAgent`. This is acceptable for now but inconsistent.
- **Persistence**: The `load_state` implementation focuses on basic assets/inventory. Full persistence (restoring `BioState`, `HRState`, etc.) requires a more comprehensive serialization strategy beyond `AgentStateDTO`.
