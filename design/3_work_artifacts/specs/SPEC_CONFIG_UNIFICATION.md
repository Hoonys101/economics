# Report: TD-166 Configuration Duality Analysis

## Executive Summary
The current configuration system is a fragmented and brittle mix of a monolithic Python file (`config.py`) and several duplicative YAML files. This report proposes a unified, component-based configuration pattern that aligns with the ECS architecture, centralizes management, and enables dynamic configuration.

## Detailed Analysis

### 1. Configuration Monolith
- **Status**: ❌ Problem Identified
- **Evidence**: `config.py` is a large file containing over 500 lines of global constants. It mixes engine-level settings (e.g., `SIMULATION_TICKS`) with agent-specific attributes (e.g., `INITIAL_HOUSEHOLD_NEEDS_MEAN`).
- **Notes**: This makes configuration difficult to navigate, manage, and safely modify. The global nature of these settings creates tight coupling between the engine and all agents.

### 2. Fragmentation and Duplication
- **Status**: ❌ Problem Identified
- **Evidence**: Configuration parameters are duplicated between `config.py` and YAML files such as `config/economy_params.yaml`. For instance, `NEWBORN_INITIAL_NEEDS` is defined in both locations.
- **Notes**: This creates ambiguity about the "source of truth" and increases the risk of inconsistencies, where a change in one file is not reflected in the other.

### 3. Ambiguous Loading Hierarchy
- **Status**: ❌ Problem Identified
- **Evidence**: There is no discernible mechanism for hierarchical configuration loading. It is unclear whether values in `config.py` override YAML files, or vice-versa.
- **Notes**: This lack of a clear precedence order makes the behavior of the system unpredictable and difficult to debug.

### 4. Agent Configuration Coupling
- **Status**: ⚠️ Partial Implementation
- **Evidence**: The use of `HouseholdConfigDTO` in `modules/household/api.py` is a good step towards structured agent configuration. However, the source of the data for this DTO is likely the monolithic `config.py`, which undermines the decoupling by forcing agent-specific definitions into a global scope.
- **Notes**: While the DTO provides a clean interface for components, its reliance on a global configuration file maintains a high degree of coupling.

## Risk Assessment
- **High Risk of Error**: The current system is prone to configuration-related bugs due to inconsistency and lack of clarity.
- **Low Scalability**: As the number of agent types and configuration parameters grows, the monolithic `config.py` will become increasingly unmanageable.
- **Poor Experimentation Support**: The static and fragmented nature of the configuration makes it cumbersome to run experiments with different parameters or scenarios.

## Proposed Solution: A Unified ECS Configuration Pattern

### 1. Centralized Configuration Schema
- **Action**: Define a comprehensive configuration schema using a library like Pydantic. This creates a single, version-controlled source of truth for all possible parameters.
- **Benefit**: Type validation, clear documentation, and discoverability of all configuration options.

### 2. Layered Configuration Loading
- **Action**: Implement a configuration loader that merges settings from multiple sources with a clear order of precedence:
    1.  **Base Defaults** (defined in the Pydantic schema).
    2.  **Engine Configuration File** (e.g., `config/engine.yaml`).
    3.  **Scenario Configuration File** (e.g., `config/scenarios/my_scenario.yaml`).
    4.  **Environment Variables** (for runtime overrides).
- **Benefit**: Provides flexibility and a clear hierarchy, separating base settings from scenario-specific modifications.

### 3. ECS `Configuration` Component
- **Action**: Create a `Configuration` component within the ECS framework. When an entity (agent) is created, a `Configuration` component is attached to it.
- **Benefit**: This treats configuration as a first-class citizen of the ECS architecture. It allows for agent-specific overrides and dynamic modification of configuration at runtime.

### 4. Implementation Flow
1.  On startup, the **Configuration Loader** builds a master configuration object from the various sources.
2.  When a new agent entity is created, the **Agent Factory** reads the relevant section of the master configuration.
3.  A `Configuration` component is added to the agent entity, populated with its specific settings.
4.  Systems within the engine can query the `Configuration` component of an entity to access its parameters, ensuring they always have the correct, context-specific values.

## Conclusion
The current configuration system is a significant source of technical debt and risk. Migrating to a unified, component-based pattern will improve reliability, scalability, and flexibility. This approach respects the existing ECS architecture and provides a robust foundation for future development and experimentation.
