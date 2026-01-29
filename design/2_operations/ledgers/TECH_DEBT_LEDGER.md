# Technical Debt Ledger

This document tracks technical debt identified during the development process. Each entry includes a description of the problem, its impact, a proposed solution, and its priority.

## Outstanding Debt

# TD-118: Standardize Inventory Access
- **Problem**: In `modules/analysis/storm_verifier.py`, there's a TODO comment indicating inventory access as a dictionary needs to be standardized. This suggests inconsistent inventory structures across agent types (e.g., Household, Firm).
- **Impact**: Makes it difficult for analysis modules to reliably access inventory data, potentially leading to errors or inconsistent behavior.
- **Proposed Solution**: Define a common interface or DTO for inventory access across all agents that hold inventory. Ensure all agents (Households, Firms, etc.) expose their inventory via this standardized mechanism (e.g., a dictionary, a dedicated Inventory object with well-defined methods).
- **Priority**: Medium

# TD-122: Unstable Test Suite
- **Problem**: The project's test suite is currently unstable, requiring isolated execution scripts for new features.
- **Impact**: Increases the risk of regressions and makes continuous integration difficult.
- **Proposed Solution**: Stabilize the test suite by addressing flaky tests and ensuring consistent test environments.
- **Priority**: High

# TD-140: God Object (SimulationRepository)
- **Problem**: `SimulationRepository` acts as a monolithic data access object.
- **Impact**: Violation of Single Responsibility Principle, difficult to maintain and test.
- **Proposed Solution**: Decompose `SimulationRepository` into domain-specific repositories.
- **Status**: In Progress (WO-140)

# TD-141: God File (corporate_manager.py)
- **Problem**: `corporate_manager.py` contains low-cohesion modules and excessive logic.
- **Impact**: Hard to maintain, test, and extend.
- **Proposed Solution**: Refactor into smaller, focused modules.
- **Priority**: High

# TD-142: God File (ai_driven_household_engine.py)
- **Problem**: `ai_driven_household_engine.py` is complex and lacks cohesion.
- **Impact**: Difficult to understand and modify household decision logic.
- **Proposed Solution**: Refactor into smaller components (e.g., ConsumptionManager, LaborManager).
- **Priority**: High

# TD-149: Loosen Coupling between Simulation Core and Observer/Injector Modules
- **Problem**: `StormVerifier` and `ShockInjector` modules directly access internal implementation details of the `simulation` object (e.g., `_simulation.central_bank`, `_simulation.firms`).
- **Impact**: Creates tight coupling, making it harder to refactor the simulation core without affecting these analysis/injection modules. Reduces modularity and testability.
- **Proposed Solution**: Introduce `Protocol` interfaces (e.g., `ISimulationState` or `ISimulationAPI`) that the main `simulation` object implements. These interfaces should explicitly define the subset of attributes and methods that external modules like `StormVerifier` and `ShockInjector` are allowed to access. The `__init__` methods of `StormVerifier` and `ShockInjector` should then type-hint against these protocols.
- **Priority**: High
