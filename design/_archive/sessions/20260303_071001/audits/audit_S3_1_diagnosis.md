# Insight Report: audit-mock-leak-diagnosis

## [Architectural Insights]
- **State Pollution in `conftest.py`**: The `mock_config_module` fixture (`L17-24`) utilizes a shallow copy pattern (`setattr(mock_config, key, getattr(config, key))`) to mirror the global `config` module. This is identified as "Duct-Tape Debugging," as it binds the test environment's configuration to the global state at runtime, violating the "Clean Room" isolation principle.
- **Disconnected Dependency Injection**: Fixtures `simple_household` and `simple_firm` request `mock_config_module` as a dependency but fail to pass this mock to the `create_household` and `create_firm` factories (`L28`, `L41`). This confirms that the factories are either defaulting to the global `config` module or using separate, potentially un-mocked, DTOs, rendering the fixture redundant and misleading.
- **Hidden Registry Risks**: The usage of `create_household` and `create_firm` without an explicit `registry` or `simulation` context strongly implies that these factories interact with a global `Simulation` singleton. In the absence of a `Simulation.clear()` or `teardown` fixture in `conftest.py`, state accumulation across integration tests is guaranteed, leading to circular dependency leaks and non-deterministic failures.

## [Regression Analysis]
- **Isolation Integrity**: The current diagnostic setup is highly susceptible to "State Leakage." Any modification to the global `config` in one test scenario will propagate to others via the flawed `mock_config_module` copy.
- **Test Interference**: Entities created with static IDs (1, 101) will collide in the global registry if multiple integration tests are executed in the same session without registry flushing.

## [Test Evidence]
*Audit conducted via static analysis of `tests/integration/scenarios/diagnosis/conftest.py` as per Technical Reporter persona.*
- **Observation**: No explicit simulation context is passed to factories.
- **Verification**: `mock_config_module` is unused in actual entity instantiation (`L28`, `L41`).
- **Conclusion**: The setup provides an illusion of isolation while maintaining a hidden dependency on global state.

***

# Forensic Audit: Scenario Diagnosis (audit-mock-leak-diagnosis)

## Executive Summary
The forensic audit of `tests/integration/scenarios/diagnosis/conftest.py` identifies critical architectural risks including **State Pollution** and **Hidden Global Registry Leaks**. The diagnostic fixtures provide false isolation by mirroring global configuration state and fail to decouple entity creation from the global simulation context.

## Detailed Analysis

### 1. Hidden Circular Dependencies & Registry Leaks
- **Status**: ❌ Missing Isolation
- **Evidence**: `conftest.py:L26-53`
- **Notes**: The factories `create_household` and `create_firm` are invoked without an injected registry. This pattern typically indicates a hidden dependency on a global `Simulation` singleton. Without explicit teardown logic in the conftest, entity IDs and assets will persist or collide across test scenario runs.

### 2. State Pollution (Config Mocking)
- **Status**: ⚠️ Partial / "Duct-Tape"
- **Evidence**: `conftest.py:L17-24`
- **Notes**: The `mock_config_module` fixture mirrors the actual `config` module attributes via iteration. This "Duct-Tape" approach captures the global state at initialization, causing "Mock Drift" if the environment changes. Furthermore, the mock is requested by fixtures but ignored in factory calls, proving the isolation is non-functional.

### 3. Protocol & DTO Compliance
- **Status**: ✅ Implemented
- **Evidence**: `conftest.py:L28, L41`
- **Notes**: The use of `create_household_config_dto` and `create_firm_config_dto` adheres to the **DTO Purity** mandate for cross-boundary data transfer, though the values within these DTOs remain coupled to global defaults.

## Risk Assessment
- **Vibe Assessment (High Risk)**: The implementation of `mock_config_module` is a clear example of "Duct-Tape Debugging." It attempts to mask global dependencies rather than refactoring the code to support proper dependency injection.
- **Architectural Debt**: The disconnection between requested mocks and factory parameters suggests significant technical debt in the testing utility layer (`tests.utils.factories`).

## Conclusion
The diagnostic setup in `conftest.py` is architecturally unsound. It creates a hidden link between the integration scenarios and the global simulation state, which will eventually manifest as intermittent "State Pollution" failures. Immediate refactoring is required to ensure factories accept an explicit registry/simulation context and that the `config` is properly patched rather than copied.