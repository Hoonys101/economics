# Work Order: TD-066 - Refactoring `Simulation` God Class

**Phase:** 29 (Refinement)
**Priority:** HIGH
**Prerequisite:** `TD-065` (Household Refactor Spec)

## 1. Problem Statement
The `Simulation` class in `simulation/engine.py` has grown to over 900 lines of code, becoming a "God Class" that manages state, orchestrates the simulation loop, and contains disparate system-level logic. This violates the Single Responsibility Principle (SRP), making the simulation engine difficult to maintain, test, and extend. It is tightly coupled with numerous sub-systems, creating a fragile architecture where changes have unpredictable side effects, as identified in technical debt item `TD-066`.

## 2. Objective
Decompose the `Simulation` class into a set of cohesive, specialized components. The `Simulation` class will be refactored into a **Facade**, preserving its public API to maintain 100% backward compatibility with entry points (`main.py`) and the entire test suite. This refactoring will establish a clear, unidirectional data flow using immutable DTOs, mitigating architectural risks and improving modularity.

## 3. Target Architecture
The `Simulation` class will delegate its responsibilities to a set of new, internal components. It will act as the public-facing entry point, while the internal complexity is managed by these specialized classes.

*   **`Simulation` (The Facade)**:
    *   Maintains the public API (`__init__`, `run_tick`, `finalize_simulation`).
    *   Owns and initializes `WorldState`, `TickScheduler`, and other core components.
    *   Delegates the `run_tick` call to the `TickScheduler`.
    *   Ensures backward compatibility for all external callers.

*   **`WorldState` (State Manager)**:
    *   The single source of truth for all simulation state (agents, firms, markets, time, etc.).
    *   Responsibilities: Managing agent registries, providing accessors for state, and generating immutable `TickStateDTO` snapshots for use by other systems. Direct mutation of this component from outside is forbidden.

*   **`TickScheduler` (Orchestrator)**:
    *   Replaces the monolithic `run_tick` method.
    *   Owns the logic for the sequence of operations within a single tick.
    *   Implements a multi-stage pipeline to preserve the critical causal chain of the simulation.
    *   Coordinates the flow of data: requests a `TickStateDTO` from `WorldState`, passes it to various systems, collects `ActionDTOs` in return, and sends them to the `ActionProcessor`.

*   **`ActionProcessor` (State Mutator)**:
    *   The *only* component authorized to mutate `WorldState`.
    *   Receives a list of `ActionDTOs` from the `TickScheduler`.
    *   Applies the actions sequentially to the `WorldState`, ensuring atomic and consistent state transitions.

*   **Existing Systems (`HousingSystem`, `FirmSystem`, etc.)**:
    *   These will be refactored to be stateless.
    *   They will no longer receive the `simulation` instance.
    *   Their `process()` methods will be updated to accept an immutable `TickStateDTO` and return a list of `ActionDTOs`.

**Unidirectional Data Flow:**
`WorldState` -> `TickStateDTO` -> `TickScheduler` -> `System` -> `ActionDTO[]` -> `ActionProcessor` -> `WorldState`

---

## 4. Implementation Plan

### Track A: DTO & Interface Definition (`modules/simulation_engine/api.py`)

1.  **Create `modules/simulation_engine/dtos.py`**:
    *   **`TickStateDTO`**: A read-only Pydantic model (or similar immutable structure) containing a snapshot of all data needed for a tick (e.g., `time`, `households`, `firms`, `markets`, `government_state`). This will be designed to anticipate the `HouseholdStateDTO` from `TD-065`.
    *   **`ActionDTO`**: A base class for representing desired state changes.
        *   Subclasses: `UpdateAssetAction(agent_id, delta)`, `CreateAgentAction(agent_data)`, `PlaceOrderAction(order_data)`, `LogAction(message, level)`.

2.  **Create `modules/simulation_engine/interfaces.py`**:
    *   Define abstract base classes: `IWorldState`, `ITickScheduler`, `IActionProcessor` to formalize the contracts between components.

### Track B: Core Component Implementation

1.  **Create `modules/simulation_engine/world_state.py`**:
    *   Implement `WorldState`, holding all agent lists and other global states.
    *   Implement `create_tick_state_dto() -> TickStateDTO`.
    *   Implement internal methods for state mutation, to be called *only* by the `ActionProcessor` (e.g., `_update_agent_assets`).

2.  **Create `modules/simulation_engine/action_processor.py`**:
    *   Implement `ActionProcessor`.
    *   Implement `process_actions(world_state: IWorldState, actions: List[ActionDTO])`. This method will contain a mapping from `ActionDTO` types to the corresponding mutation method in `WorldState`.

3.  **Create `modules/simulation_engine/tick_scheduler.py`**:
    *   Implement `TickScheduler`. This is the most critical part.
    *   The `run_tick` method will be structured into a clear, sequential pipeline that mirrors the existing logic.

    **Proposed Tick Pipeline:**
    | Stage | Original `run_tick` Section | Responsibilities |
    | :--- | :--- | :--- |
    | **1. Initialization** | L213-228 | Increment time, Chaos/Event Injection, `run_public_education` |
    | **2. Pre-Decision Update**| L228-340 | Bank/Firm interest & profit distribution, Tracker update, Social rank update |
    | **3. Sensory & Policy**| L286-370 | `SensorySystem` data generation, Government policy decisions, Central Bank update |
    | **4. Agent Decision** | L378-520 | Households and Firms `make_decision` calls, generating orders. |
    | **5. Market Matching** | L522-540 | Matching orders in all markets (goods, stocks, housing). |
    | **6. Consumption & Prod.** | L542-700 | `CommerceSystem`, Technology update, Housing processing, Agent production. |
    | **7. Lifecycle Events** | L630-650, L799-810 | `LifecycleManager`, `MAManager`, entrepreneurship checks. |
    | **8. Finalization** | L702-end | AI learning updates, state persistence, counter resets, money supply verification. |

### Track C: `Simulation` Facade Refactoring

1.  **Modify `simulation/engine.py`**:
    *   Remove all internal logic from the `Simulation` class.
    *   In `__init__`, instantiate `WorldState`, `TickScheduler`, `ActionProcessor`, and all other systems. Pass component instances to each other as needed (e.g., `TickScheduler` needs `WorldState` and `ActionProcessor`).
    *   Refactor `run_tick()` to be a single call: `self.scheduler.run_tick()`.
    *   Refactor `finalize_simulation()` to delegate to the `PersistenceManager` and other relevant components.

### Track D: Satellite System Refactoring

1.  **Update all relevant systems** (e.g., `HousingSystem`, `MAManager`, `FinanceSystem`, `EventSystem`).
2.  Change method signatures from `process(simulation: Simulation)` to `process(state: TickStateDTO) -> List[ActionDTO]`.
3.  Remove all direct access to `simulation.households`, `simulation.firms`, etc., and read data only from the incoming `state` DTO.
4.  Instead of directly mutating state, return a list of `ActionDTOs` describing the desired changes.

---

## 5. Verification Plan

1.  **Backward Compatibility**: The Facade pattern ensures that `main.py`, `run_experiment.py`, and all high-level verification scripts will run without modification.
2.  **Integration Tests**: The existing test suite (`tests/`) will serve as the primary integration and regression test. A 100% pass rate is mandatory. The preservation of the `Simulation` facade's API is key to this.
3.  **Component Unit Tests**: New unit tests must be created for `WorldState`, `TickScheduler`, and `ActionProcessor` to test their logic in isolation.
    *   `test_tick_scheduler.py` will verify the sequence of calls.
    *   `test_action_processor.py` will verify that `ActionDTOs` correctly mutate a mock `WorldState`.

---

## 6. 🚨 Risk & Impact Audit (Mitigation Plan)

*   **Risk: God Class Symbiosis (`Simulation` and `Household`)**
    *   **Finding**: The `Simulation` class is deeply coupled with the `Household` "God Class" (`TD-065`).
    *   **Mitigation**: This refactoring **must** proceed with the `TD-065` specification in mind. The new `TickStateDTO` will be designed to contain a list of `HouseholdStateDTO`s, not monolithic `Household` objects. The new `AgentLifecycleManager` (if extracted) will be designed to interact with the future `Household.BioComponent` via DTOs, ensuring future compatibility.

*   **Risk: The Orchestration Hydra of `run_tick`**
    *   **Finding**: The execution order within `run_tick` is a critical and non-arbitrary causal chain.
    *   **Mitigation**: The `TickScheduler` is mandated to implement a multi-stage sequential pipeline as detailed in the Implementation Plan (Track B). This preserves the exact logical flow, preventing causality violations. The stages will be clearly defined methods (`_run_initialization_stage`, `_run_decision_stage`, etc.) called in order.

*   **Risk: Creating a New God Object ("WorldState")**
    *   **Finding**: Simply moving state into a `WorldState` object that is passed around and mutated directly would recreate the problem.
    *   **Mitigation**: A strict, **unidirectional data flow using immutable DTOs** is mandated. Systems are forbidden from mutating state directly. They receive a `TickStateDTO` and return `ActionDTOs`. Only the `ActionProcessor` can apply these changes to the `WorldState`, creating a controlled and traceable mutation process.

*   **Constraint: The Facade Pattern is Non-Negotiable**
    *   **Finding**: The `Simulation` class API is the public contract for the entire engine. Breaking it will break all tests and entry points.
    *   **Mitigation**: The `Simulation` class **must** be retained as a public Facade. The refactoring will occur *inside* this class, invisible to external callers. The `run_tick` method will be reduced to a single line delegating to the internal `TickScheduler`, guaranteeing 100% backward compatibility.

---
## 7. Mandatory Reporting (Jules's Guideline)
During implementation, any unforeseen challenges, architectural friction, or potential improvements discovered must be logged as a new entry in `communications/insights/`. Any identified technical debt must be proposed for inclusion in `design/TECH_DEBT_LEDGER.md`.
