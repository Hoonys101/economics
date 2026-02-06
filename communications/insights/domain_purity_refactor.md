# Technical Insight Report: Domain Purity & Housing Saga Refactoring

## 1. Problem Phenomenon
The transaction and saga systems were suffering from strong coupling and leaky abstractions. Specifically:
- **God Class Violations**: `SettlementSystem` and AI managers were directly accessing internal agent properties (`agent.assets`), creating fragile dependencies on implementation details (legacy `dict` vs `float` assets).
- **Leaky DTOs**: `HousingTransactionSagaStateDTO` contained raw agent IDs that required repeated and inconsistent resolution logic scattered across handler methods.
- **Tight Coupling**: `HousingTransactionSagaHandler` was tightly coupled to the concrete `HousingService`, preventing the abstraction of inventory management for other asset types.

## 2. Root Cause Analysis
- **Lack of Canonical Accessor**: There was no unified utility to access agent financial assets, leading to `isinstance` checks and `hasattr` checks proliferated across the codebase (e.g., `AITrainingManager`).
- **DTO Design Flaws**: Saga DTOs were designed as "pointers" (holding IDs) rather than "containers" (holding context), forcing handlers to fetch state from the simulation engine repeatedly.
- **Missing Interface Layer**: The `HousingService` was used directly by the Saga Handler, violating the Dependency Inversion Principle.

## 3. Solution Implementation Details
The refactoring was executed in three phases:

### Phase 1: DTO Purity (TD-255)
- Introduced `HousingSagaAgentContext` to capture a snapshot of agent state (ID, income, debt) at the start of a saga.
- Refactored `HousingTransactionSagaHandler._handle_initiated` to populate this context once.
- Updated subsequent saga steps (`_handle_escrow_locked`, etc.) to rely on this context, reducing reads from the global simulation state.

### Phase 2: Inventory Abstraction (TD-256)
- Defined the `IInventoryHandler` Protocol in `modules/inventory/api.py`, abstracting asset operations (`lock_asset`, `release_asset`, `transfer_asset`, `add_lien`).
- Implemented this interface in `HousingService`.
- Decoupled `HousingTransactionSagaHandler` from `HousingService` by depending on `IInventoryHandler`.

### Phase 3: Asset Access Unification (TD-259)
- Created `modules/finance/util/api.py` exporting `get_asset_balance`.
- This utility handles the polymorphism of `agent.assets` (legacy dict vs float) and `agent.wallet` centrally.
- Refactored `AITrainingManager` to use this utility, eliminating fragile lambda functions and type checks.

## 4. Lessons Learned & Technical Debt Identified
- **Lesson**: "Context" DTOs significantly simplify saga handlers by reducing the need for side-effect-prone lookups during execution.
- **Lesson**: Protocol-based interfaces in Python allow for flexible decoupling without strict inheritance hierarchies, useful for retrofitting interfaces onto existing services like `HousingService`.
- **Remaining Debt**:
    - `SettlementSystem` still has some saga orchestration logic that should be moved to a dedicated `SagaOrchestrator` (TD-253).
    - Other AI managers and evaluators might still have scattered asset access patterns that were not caught in this pass.
    - The "Centralized Monetary Authority" (TD-258) pattern was partially prepared for but not fully enforced in this mission.
