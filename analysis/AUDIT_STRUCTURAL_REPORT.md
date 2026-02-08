# Structural Audit Report

## 1. Executive Summary
This report details the findings of a structural audit performed on the `simulation` module. The audit focused on identifying "God Classes" (classes exceeding 800 lines of code) and "Abstraction Leaks" (raw agent objects being passed into decision engines or other components).

## 2. Findings

### 2.1. God Classes (>800 LOC)

*   **`simulation/firms.py` (Firm)**: 878 lines.
    *   **Description:** The `Firm` class has grown significantly, handling core logic, state management, and orchestrating multiple engines (Production, HR, Finance, Sales). It also contains a large `_execute_internal_order` method that acts as a command dispatcher for various internal actions.
    *   **Recommendation:** Refactor `_execute_internal_order` into a dedicated `FirmOrderProcessor` component. Delegate inventory management to `InventoryManager`.

*   **`simulation/agents/government.py` (Government)**: 709 lines.
    *   **Description:** While under the 800-line threshold, the `Government` class is large and complex, handling fiscal policy, social policy, infrastructure, and legacy welfare logic.
    *   **Recommendation:** Monitor growth. Refactor policy decision-making to use DTOs to reduce coupling.

### 2.2. Abstraction Leaks

*   **Government Policy Engine Leak**
    *   **Location:** `simulation/agents/government.py` -> `IGovernmentPolicy.decide(self, government, ...)`
    *   **Issue:** The raw `Government` agent object is passed directly to the policy engine (`TaylorRulePolicy`, `AdaptiveGovPolicy`). This allows the policy engine to arbitrarily modify the agent's state, violating encapsulation and making the system harder to test and reason about.
    *   **Recommendation:** Introduce `PolicyContextDTO` to pass only necessary data (sensory inputs, current state) and `PolicyDecisionResultDTO` to return policy decisions and state updates.

*   **Firm Inventory Leak**
    *   **Location:** `simulation/firms.py` -> `ProductionEngine.produce(..., inventory_handler=self, ...)`
    *   **Issue:** The `Firm` object (acting as `IInventoryHandler`) is passed to the `ProductionEngine`. While it adheres to the interface, passing `self` exposes the entire agent if the engine were to cast it.
    *   **Recommendation:** Use `InventoryManager` via composition and pass the manager instance instead of `self`.

*   **Firm HR Leak**
    *   **Location:** `simulation/firms.py` -> `HREngine.fire_employee(..., firm=self, ...)`
    *   **Issue:** The `Firm` object is passed to `fire_employee`.
    *   **Recommendation:** Investigate if `fire_employee` requires the full agent or just specific components (like Wallet, ID). (Addressed in future refactoring).

## 3. Action Plan

1.  **Refactor Government Policy:** Implement DTO-based communication between `Government` and `IGovernmentPolicy`.
2.  **Refactor Firm Inventory:** Integrate `InventoryManager` into `Firm` and pass it to engines.
3.  **Refactor Firm Order Processing:** Extract `_execute_internal_order` into `FirmOrderProcessor` to reduce `Firm` class size.
