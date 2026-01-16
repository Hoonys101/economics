# Work Order WO-079 Pre-flight Audit: Config Automation

## Executive Summary
This report outlines the feasibility and strategic path for migrating hardcoded constants to a centralized YAML-based configuration system. The refactoring is not only feasible but essential for improving project maintainability. The primary risk lies in managing the transition without breaking the existing test suite, which can be mitigated through a phased, hybrid approach. Circular dependency risks are low, provided the new configuration loader remains an independent utility.

## Detailed Analysis

### 1. Circular Dependency Risk
- **Status**: ✅ Low Risk
- **Evidence**: A new configuration loader (e.g., `ConfigManager`) can be implemented as a self-contained utility within `simulation/`. This manager would be responsible for reading `.yaml` files from the `config/` directory and exposing the values as a Python object.
- **Notes**: As long as this new utility does not import other simulation modules (e.g., `engine`, `core_agents`), it will act as a leaf node in the dependency graph, preventing circular imports. Core modules like `engine.py` and `core_agents.py` will import this utility, which is a safe, unidirectional dependency.

### 2. Implementation Path
- **Status**: ✅ Clear Path Identified
- **Evidence**: A phased migration is recommended to ensure stability and accommodate testing.
- **Implementation Plan**:
    1.  **Introduce Config Loader**: Create a new module (e.g., `simulation/config_manager.py`) with a class that loads all `.yaml` files from the `config/` directory into a single, accessible configuration object.
    2.  **Hybrid Configuration Object**: In `simulation/initialization/initializer.py`, instantiate the new `ConfigManager`. For backward compatibility, the existing `config_module` (from `config.py`) should also be loaded, with YAML values taking precedence over Python module values. This allows for a gradual transition.
    3.  **Incremental Migration**:
        *   Identify and move hardcoded constants from a single module (e.g., `simulation/bank.py`) to a new YAML file (e.g., `config/finance.yaml`).
        *   Update the Python module to source the value from the new config object instead of a hardcoded value or the old `config_module`.
        *   Repeat for all target files (`engine.py`, AI modules, agent modules), organizing constants into logical YAML files (`ai.yaml`, `agents.yaml`, etc.).
    4.  **Test Adaptation**: Update unit and integration tests to mock the `ConfigManager` or provide temporary YAML files via `tmp_path` fixtures. This is the most critical and time-consuming step.
    5.  **Deprecation**: Once all constants are migrated, the legacy `config.py` loading mechanism can be safely removed.

### 3. Externalizable "God Class" Attributes
- **Status**: ✅ Attributes Identified
- **Evidence**: Multiple modules, particularly `simulation.engine`, agent definitions, and AI modules, contain hardcoded "magic numbers" and parameters that should be managed as configuration.
- **Identified Candidates for Externalization**:

| File | Line(s) | Constant(s) / Attribute(s) | Recommended Config Key |
| :--- | :--- | :--- | :--- |
| `simulation/engine.py` | `L113` | `batch_save_interval: int = 50` | `simulation.batch_save_interval` |
| `simulation/engine.py` | `L115-119` | `deque(maxlen=10)` for buffers | `simulation.sma_buffer_window` |
| `simulation/engine.py` | `L173-183` | Tick numbers and shock values for Chaos Events | `simulation.chaos_events` |
| `simulation/ai/action_selector.py`| `L27-30` | Epsilon decay parameters (`initial`, `final`, `decay_steps`) | `ai.epsilon_decay` |
| `simulation/ai/household_ai.py` | `L20` | `AGGRESSIVENESS_LEVELS` | `ai.household.aggressiveness_levels` |
| `simulation/ai/household_ai.py` | `L48` | `asset_bins = [100.0, ...]` | `ai.household.state_bins.assets` |
| `simulation/ai/firm_ai.py` | `L22` | `AGGRESSIVENESS_LEVELS` | `ai.firm.aggressiveness_levels` |
| `simulation/ai/firm_ai.py` | `L44-64` | Discretization bins for state calculation | `ai.firm.state_bins` |
| `simulation/bank.py` | `L11-14` | `TICKS_PER_YEAR`, `INITIAL_BASE_ANNUAL_RATE`, etc. | `finance.bank_defaults` |
| `simulation/policies/smart_leviathan_policy.py`|`L40-42`|`TAX_STEP`, `RATE_STEP`, `BUDGET_STEP`|`government.policy.step_sizes`|
| `simulation/systems/firm_management.py`|`L24,31,34`|`STARTUP_COST`, `ENTREPRENEURSHIP_SPIRIT`, `VISIONARY_MUTATION_RATE`|`firm.startup`|

## Risk Assessment
- **High Risk**: **Test Failures**. The existing test suite heavily relies on the current Python-based `config_module`. Changing how configuration is loaded and accessed will break many tests. **Mitigation**: A dedicated phase of the refactoring must be allocated to updating tests, using `pytest` fixtures (`monkeypatch`, `mocker`) to inject test-specific configurations without altering YAML files.
- **Medium Risk**: **Incomplete Migration**. Some "magic numbers" may be missed during the refactoring, leading to a partially configured system. **Mitigation**: After the main refactoring, perform a codebase search for hardcoded numerical literals in the affected modules to catch any remaining values.
- **Low Risk**: **Performance**. Loading from YAML files at startup is a negligible one-time cost and will not impact simulation runtime performance.

## Conclusion
The migration to a YAML-based configuration is a crucial architectural improvement. The outlined implementation path provides a structured and safe way to execute this refactoring. The most significant effort will be the systematic and careful update of the test suite to align with the new configuration system. The risk of circular dependencies is minimal and easily avoidable.
