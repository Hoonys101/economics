# Technical Debt: DTO Refactor and Standardization

**Mission Key:** DTO_Refactor
**Date:** 2024-05-23
**Author:** Jules

## Context
The codebase is currently in a transitional state regarding Data Transfer Objects (DTOs). While `OrderDTO` has been standardized as a Dataclass, other critical DTOs like `MarketSnapshotDTO` and `SystemStateDTO` are defined as `TypedDict` in some places and used as objects in others. Furthermore, there is a naming collision for `MarketSnapshotDTO` between `modules/system/api.py` (Agent-facing market signals) and `modules/simulation/api.py` (Observer-facing macro indicators).

## Identified Technical Debt

### 1. Dual Definition of `MarketSnapshotDTO`
- **modules/system/api.py**: Defines `MarketSnapshotDTO` as a `TypedDict` containing detailed market signals (`market_signals`). Used by `DecisionContext` for agents.
- **modules/simulation/api.py**: Defines `MarketSnapshotDTO` as a `TypedDict` containing macro indicators (`gdp`, `cpi`). Used by `Simulation` engine for logging.
- **Impact**: Confusion in `simulation/engine.py` and decision engines. `DecisionContext` imports from `system/api`, while `engine.py` imports from `simulation/api`. This leads to `AttributeError` or `KeyError` if usage is mixed.

### 2. TypedDict vs Dataclass Inconsistency
- The project is moving towards Dataclasses (e.g., `OrderDTO`), but many internal DTOs remain `TypedDict`.
- **Impact**: Inconsistent access patterns (e.g., `d['key']` vs `d.key`). Dataclasses offer better type safety and method support.

### 3. Return Type Ambiguity in Decision Engines
- Decision engines return `Tuple[List[Order], Any]`. The second element (`metadata` or `tactic`) varies by implementation and is not type-safe.
- **Impact**: Difficult to extend or introspect the decision output.

### 4. Legacy Dictionary Usage
- `market_data` is passed as a raw dictionary (`Dict[str, Any]`) throughout the system.
- **Impact**: While out of scope for this specific refactor, it remains a significant source of implicit coupling and potential runtime errors.

## Refactoring Strategy

### 1. Resolve Naming Collision
- Rename `modules/simulation/api.py:MarketSnapshotDTO` to `EconomicIndicatorsDTO` (or `MacroSnapshotDTO`).
- Keep `modules/system/api.py:MarketSnapshotDTO` for agent signals.

### 2. Standardize to Dataclasses
- Convert `MarketSnapshotDTO`, `MarketSignalDTO`, `EconomicIndicatorsDTO`, and `SystemStateDTO` to `@dataclass`.
- This enforces dot notation access (`obj.field`) and provides a clear schema.

### 3. Introduce `DecisionOutputDTO`
- Replace the tuple return type in decision engines with a standardized `DecisionOutputDTO(orders: List[OrderDTO], metadata: Any)`.

### 4. Update Engine and Orchestration
- Update `simulation/engine.py` to use `EconomicIndicatorsDTO` for logging.
- Update `simulation/orchestration/phases.py` to construct proper Dataclass instances for `DecisionContext`.
