# Technical Insight Report: TD-255 Cockpit Command Refactoring

## 1. Problem Phenomenon
The legacy cockpit system allowed external scripts (and potentially the user interface) to modify the simulation state directly and synchronously.
This manifested as:
-   **Untraceable State Changes**: State modifications occurred outside the event loop, making it impossible to reconstruct the sequence of events leading to a specific state.
-   **Race Conditions**: Direct modifications could occur mid-tick or during sensitive phases, potentially violating invariants.
-   **Lack of Audit Trail**: There was no structured log of manual interventions.

## 2. Root Cause Analysis
The root cause was a lack of a formalized command pipeline for manual interventions. The `WorldState` was treated as a mutable global object accessible from anywhere, violating the Command Pattern and Event Sourcing principles that the rest of the simulation attempts to follow.

## 3. Solution Implementation Details
We implemented an asynchronous System Command Pipeline:
1.  **Command DTOs**: Defined `SystemCommand` (Union of `SetTaxRateCommand`, `SetInterestRateCommand`) in `modules/governance/api.py` to encapsulate intent.
2.  **Command Queue**: Added `system_command_queue` to `WorldState` to buffer commands received from external sources.
3.  **Command Phase**: Introduced `Phase_SystemCommands` in the `TickOrchestrator` (running early in the tick) to process these commands in a deterministic manner.
4.  **Processor**: Implemented `SystemCommandProcessor` to execute the commands and apply changes to the `SimulationState`.

This ensures that all manual interventions are:
-   **Queued**: They happen at a specific point in the simulation lifecycle.
-   **Logged**: The processor logs every execution.
-   **Type-Safe**: DTOs ensure payload validity.

## 4. Lessons Learned & Technical Debt Identified
-   **Testing Infrastructure**: The existing test suite heavily relies on synchronous state modification. Migrating these tests to use the new async command pipeline will be a significant effort (`TD-256`).
-   **DTO Proliferation**: We are accumulating many DTOs. We need to ensure strict organization to prevent circular dependencies, as seen with `SimulationState` vs `SystemCommand`.
-   **Agent Access**: The processor currently modifies agent attributes directly (e.g., `government.corporate_tax_rate`). Ideally, agents should expose methods or consume events to update their own state to maintain encapsulation.
