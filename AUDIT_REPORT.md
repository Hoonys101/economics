# Structural Audit Report

## God Classes
The following classes exceed the 800-line threshold, indicating a violation of the Single Responsibility Principle (SRP) and high complexity.

1.  **`Firm` (`simulation/firms.py`)**: ~962 lines.
    -   **Responsibility Overload**: Manages financial state, production state, HR state, inventory, and acts as an orchestrator.
    -   **Action**: Refactoring is required to delegate responsibilities to dedicated components (e.g., `InventoryManager`).

2.  **`Household` (`simulation/core_agents.py`)**: ~994 lines.
    -   **Responsibility Overload**: Manages biological needs, economic state, social standing, and decision execution.
    -   **Action**: Further decomposition into engines is already present, but the main class remains large due to state management and DTO mapping.

## Abstraction Leaks
Tracing raw agent leaks into decision engines revealed the following issues where implementation details or full agent objects are exposed unnecessarily:

1.  **`Firm` -> `ProductionEngine`**:
    -   `Firm.produce` passes `self` as `inventory_handler`. While `Firm` implements `IInventoryHandler`, passing the entire agent risks exposing unrelated state.
    -   **Critical Finding**: `ProductionEngine` accesses `state.input_inventory` (internal state) instead of using the `IInventoryHandler` interface for input materials. This leads to a disconnect because `Firm` stores purchased inputs in its main `_inventory` (via `add_item`), while `ProductionEngine` looks in a separate `input_inventory` dict, which remains empty. **This effectively prevents firms from using purchased inputs for production.**

2.  **`Firm` -> `HREngine`**:
    -   `Firm._execute_internal_order` passes `self` to `HREngine.fire_employee` as the `agent` argument for settlement transfer. `HREngine` types it as `Any`, allowing potential misuse of the agent object beyond financial capabilities.

3.  **`Government` -> `PolicyExecutionEngine`**:
    -   `PolicyExecutionEngine.execute` accepts `agents: List[Any]`. This exposes the entire simulation agent list to the execution logic, which then passes it down to `TaxService` and `WelfareManager`.
    -   **Logic Error**: `Government.make_policy_decision` calls `execution_engine.execute` with an empty list `[]` for `agents`. This likely breaks `SOCIAL_POLICY` execution (wealth tax and welfare checks) as `TaxService` attempts to iterate over an empty list.

## Recommendations
1.  **Refactor `Firm`**: Extract inventory management to `InventoryManager` and delegate calls. This reduces code size and enforces the `IInventoryHandler` boundary.
2.  **Fix `ProductionEngine`**: Update `produce` to use `inventory_handler` for both input and output, ensuring purchased materials are correctly consumed.
3.  **Refactor `PolicyExecutionEngine`**: Depend on `IAgentRepository` or specific services instead of raw lists. Fix the `Government` call site to provide access to agents (e.g., via a repository or service injection).
