# Work Order: WO-138 - Refactor Purity Verification & Test Structure

**Phase:** 3
**Priority:** HIGH
**Prerequisite:** None

## 1. Problem Statement
The project's architectural integrity and testing framework face maintainability challenges:
1.  **Purity Rules are Hardcoded**: The `scripts/verify_purity.py` script contains hardcoded lists of forbidden imports and types, making rules difficult to manage and evolve.
2.  **Test Structure is Monolithic**: The flat `tests/` directory mixes unit, integration, and scenario tests, making it hard to run targeted test suites and understand the scope of a given test.
3.  **Implicit Dependencies**: Core architectural constraints, like preventing agent access to `WorldState`, are enforced by these hardcoded rules, creating a brittle system.

This Work Order aims to refactor these components to improve maintainability, configurability, and scalability.

## 2. Objective
- Externalize purity verification rules to a central configuration file.
- Reorganize the `tests/` directory into a standard `unit/`, `integration/`, `scenarios/` structure.
- Ensure the new system continues to enforce critical architectural boundaries (e.g., the `WorldState` God Class constraint).
- Establish a clear, configurable method for defining "kernel" types like `Government` that are off-limits to low-level modules.

## 3. Implementation Plan

### Track A: Purity Rule Externalization

1.  **Modify `pyproject.toml`**: Introduce a new section `[tool.purity]` to house all configuration. This avoids creating new custom config files.

    ```toml
    # pyproject.toml

    [tool.purity]
    # Define modules that are forbidden from being imported by agent-level code.
    forbidden_imports = ["config"]

    # Define "Kernel" types that agent-level code (e.g., households, firms) cannot reference in type hints.
    # This enforces architectural boundaries and prevents access to God Classes like WorldState.
    forbidden_kernel_types = [
        "WorldState", "Simulation", "Bank", "CommerceSystem", "Economy",
        "TechnologyManager", "RefluxSystem", "Government", "CentralBank"
    ]

    # Define paths where import rules should be strictly enforced.
    check_imports_dirs = ["modules", "simulation"]

    # Define paths where type-hint rules should be strictly enforced.
    # This is the core "Purity Gate" for low-level agents.
    check_types_dirs = ["modules/household", "modules/firm"]
    check_types_files = ["simulation/core_agents.py", "simulation/firms.py"]
    ```

2.  **Refactor `scripts/verify_purity.py`**:
    -   Remove the hardcoded `FORBIDDEN_IMPORTS`, `FORBIDDEN_TYPES`, and directory path lists.
    -   Implement logic to read the `[tool.purity]` section from `pyproject.toml` using `tomllib`.
    -   The core AST-parsing logic will remain but will now be driven by the loaded configuration.

    **Pseudo-code for `verify_purity.py`:**
    ```python
    import tomllib # Or tomli for compatibility

    def load_purity_config():
        # Read pyproject.toml and return the [tool.purity] dictionary.
        # Handle file not found or section not found errors.
        ...
        return config

    def main():
        config = load_purity_config()

        # Get rule sets from config
        forbidden_imports = set(config.get("forbidden_imports", []))
        forbidden_types = set(config.get("forbidden_kernel_types", []))
        
        # Get target files from config
        files_to_check_imports = collect_files(config.get("check_imports_dirs", []))
        files_to_check_types = collect_files(config.get("check_types_dirs", []))
        files_to_check_types.update(config.get("check_types_files", []))

        # ... proceed with existing AST walking logic using these loaded variables
    ```

### Track B: Test Directory Reorganization

This is a high-risk task that requires careful execution to avoid breaking the test suite.

1.  **Create New Directory Structure**:
    -   `tests/unit/`
    -   `tests/integration/`
    -   `tests/scenarios/`

2.  **Categorize and Move Test Files**:
    -   Move files testing single classes or functions in isolation to `tests/unit/` (e.g., `test_household_needs.py`, `test_firm_production.py`).
    -   Move files testing interactions between multiple components to `tests/integration/` (e.g., `test_market_clearing.py`, `test_banking_system.py`).
    -   Move files that run the simulation for multiple ticks or test complex, multi-step behaviors to `tests/scenarios/` (e.g., `test_laffer_curve_experiment.py`).
    -   Leave `conftest.py` files in their respective directories, but the top-level `tests/conftest.py` will be crucial.

3.  **Fix Python Imports**:
    -   The move will break relative imports. A script should be used to update all test files.
    -   **Change Pattern**: `from ..simulation.models` becomes `from simulation.models`.
    -   A Python script using `pathlib` and string replacement is recommended over `sed` for cross-platform compatibility.

4.  **Update `pytest.ini`**:
    -   Ensure the `testpaths` configuration is updated to discover tests in the new subdirectories.
    ```ini
    # pytest.ini
    [pytest]
    testpaths = tests/unit tests/integration tests/scenarios
    ```

### Track C: Dynamic Agent Discovery (Registry Refactor)

1.  **Modify `simulation/world_state.py`**:
    -   Implement a `Registry` component or extend `WorldState` to support `resolve_agent_id(role: str) -> int`.
    -   Example: `world.resolve_agent_id("GOVERNMENT")` should return the current government ID.
2.  **Refactor Agents**:
    -   Purge constant references like `config.GOVERNMENT_ID` from `TaxAgency`, `CentralBank`, and `Household` logic.
    -   Replace with calls to the discovery service via the `DecisionContext`.
    -   **Rationale**: This decouples agent logic from specific instance IDs, allowing for multi-government scenarios or dynamic government replacement.

## 4. Verification

1.  **Purity Check**: Run `python scripts/verify_purity.py`. It must pass, using the new rules from `pyproject.toml`.
2.  **Full Test Suite**: Run `pytest`. All tests must be discovered and pass. No tests should be silently ignored due to pathing issues.
3.  **Manual Verification**: Manually check that a test file from each new directory (`unit`, `integration`, `scenarios`) is run by `pytest -v`.
4.  **Introduce a Violation**: Temporarily add a forbidden import (e.g., `import config`) to a file in `modules/household/` and run `verify_purity.py` to ensure it correctly fails. Revert the change afterward.

## 5. Risk & Impact Audit (Post-mortem of Pre-flight Audit)

This design directly addresses the risks identified in the pre-flight audit:

-   **`WorldState` God Class**: The `forbidden_kernel_types` in `pyproject.toml` explicitly includes `WorldState` and other kernel-level classes. The refactored `verify_purity.py` script continues to be the primary barrier preventing low-level modules from accessing it. **Risk Mitigated.**
-   **Circular Dependency Patterns**: This refactoring does not change the core logic, only where the rules are stored. The architectural pattern of using static analysis to prevent import cycles is preserved and made more explicit. **Risk Mitigated.**
-   **Test Suite Breakage**: The risk is acknowledged as high. **Track B** of the implementation plan provides a detailed, step-by-step procedure for the migration, including a dedicated step for fixing imports and verifying test discovery. This structured approach is the mitigation. **Risk Acknowledged & Mitigation Planned.**
-   **Purity Script Configuration Coupling**: The entire purpose of **Track A** is to decouple the "what" (rules in `pyproject.toml`) from the "how" (the script's execution logic). **Risk Mitigated.**

---
## 6. Jules Assignment

| Track | Task | Files to Modify |
|---|---|---|
| A | Externalize Purity Rules | `pyproject.toml`, `scripts/verify_purity.py` |
| B | Reorganize Test Directory | `tests/`, `pytest.ini` |
| C | Verify Configurable Rules | `pyproject.toml`, `scripts/verify_purity.py` |
