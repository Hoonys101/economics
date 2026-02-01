# Technical Debt: Implicit Dependency Instantiation in ViewModels

## Context
Three ViewModel classes (`AgentStateViewModel`, `EconomicIndicatorsViewModel`, `MarketHistoryViewModel`) were found to implicitly instantiate `SimulationRepository` within their constructors if a repository was not provided.

## Problem
- **Coupling**: The ViewModels were tightly coupled to the specific `SimulationRepository` implementation.
- **Testability**: Unit testing was harder because the classes created their own dependencies, requiring patching of `SimulationRepository` constructor rather than simple injection.
- **Inconsistency**: This pattern violated the Dependency Injection (DI) principle observed in `SnapshotViewModel`.

## Solution
- Refactored `__init__` methods to strictly require `SimulationRepository` as an argument.
- Removed the default `None` value and the conditional instantiation logic.
- This enforces the caller to provide the dependency, making the dependency graph explicit.

## Impact
- **Positive**: improved testability, clearer dependency graph, adherence to SOLID principles (DIP).
- **Negative**: Callers must now instantiate `SimulationRepository` before creating these ViewModels (which is desired behavior).

## References
- DI Audit Report (2026-02-01)
