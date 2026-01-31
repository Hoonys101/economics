# Insight Report: TD-173 & TD-174 Cleanup

## Preamble
- **Mission Key**: TD-173, TD-174
- **Date**: 2026-02-04
- **Author**: Jules (AI Agent)
- **Status**: IN_PROGRESS

## Phenomenon (The "What")
Two distinct technical debt items were identified for cleanup:
1.  **TD-173**: The `Household` class in `simulation/core_agents.py` contains a legacy method `decide_and_consume` which implements System 1 consumption logic. This logic has been superseded by `VectorizedHouseholdPlanner` and `CommerceSystem`.
2.  **TD-174**: The simulation engine (`simulation/engine.py` and related files) has a hardcoded `batch_save_interval` of 50. This limits the ability to tune performance and I/O frequency via configuration.

## Analysis (The "Why")
1.  **Redundant Logic**: The `decide_and_consume` method performs inventory checks and consumption updates that are now handled by `CommerceSystem.plan_consumption_and_leisure` and `CommerceSystem.finalize_consumption_and_leisure`. Retaining this method creates confusion about the actual flow of consumption logic and increases maintenance burden.
2.  **Hardcoded Constants**: Hardcoding `batch_save_interval` prevents users from adjusting the logging frequency without modifying source code. This is particularly problematic for long-running simulations where disk I/O optimization is crucial. The value was duplicated in `simulation/engine.py`, `simulation/world_state.py`, and `simulation/initialization/initializer.py`.

## Solution (The "How")
1.  **Remove Legacy Code**: Delete `decide_and_consume` from `simulation/core_agents.py`. The `consume` method is retained as it is used by `CommerceSystem` to execute the actual consumption.
2.  **Externalize Config**:
    -   Update `WorldState` to read `batch_save_interval` from `ConfigManager` (defaulting to 50 if missing).
    -   Remove hardcoded assignments in `Simulation` and `SimulationInitializer`, allowing them to rely on the centralized `WorldState` value.

## Lessons Learned
-   **Code Evolution**: As systems evolve (e.g., introduction of Vectorized Planner), legacy methods often remain as "dead code". Regular cleanup is essential to prevent "rot".
-   **Configuration Management**: Centralizing configuration access (e.g., in `WorldState` via `ConfigManager`) is more robust than scattered hardcoded values or manual property injection.
