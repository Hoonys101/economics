# ADR-004: Agent Architecture - Migration from Inheritance to Composition

## Status
Proposed

## Context
The current agent architecture relies on a `BaseAgent` abstract class from which all primary agents (`Firm`, `Household`) inherit. This class bundles multiple concerns, including financial holdings (`IFinancialEntity`), inventory management (`IInventoryHandler`), and core identity attributes.

This inheritance-based model has introduced significant friction, particularly in unit testing. As documented in `design/2_operations/ledgers/TECH_DEBT_LEDGER.md` (TDL-PH9-2), mocking properties and methods from `BaseAgent` when testing derived classes like `Firm` is difficult and brittle. The tight coupling forces tests to contend with the entire `BaseAgent` implementation rather than just the logic of the component under test.

Recent refactors to both `Firm` and `Household` have already moved them towards a component-based design internally.
- **`Firm`** now operates as an orchestrator, delegating logic to stateless engines (`HREngine`, `ProductionEngine`, etc.) that operate on dedicated state objects (`HRState`, `ProductionState`). (Evidence: `simulation/firms.py`)
- **`Household`** has been refactored into a facade that uses stateless components (`BioComponent`, `EconComponent`) and manages its state in dedicated DTOs (`BioStateDTO`, `EconStateDTO`). (Evidence: `simulation/core_agents.py`)

This evolution indicates a clear architectural drift away from inheritance and towards composition. This ADR proposes to formalize this shift.

## Decision
We will officially adopt a **"Body-Brain-State"** composition model for all agents and deprecate the `BaseAgent` inheritance pattern.

1.  **Body (The Agent Facade):** This is the main agent class (e.g., `Firm`, `Household`).
    - It will no longer inherit from `BaseAgent`.
    - It will **contain** instances of its State and its Brain(s) (Engines/Components).
    - It implements high-level interfaces (e.g., `IOrchestratorAgent`) and serves as the public API for the agent, delegating calls to its internal components.

2.  **Brain (The Logic/Engines):** These are stateless components that contain the "how-to" logic.
    - Examples: `AIDrivenHouseholdDecisionEngine`, `ProductionEngine`, `ConsumptionManager`.
    - They receive State objects as input and return new State objects or decisions as output.
    - They do not hold state themselves.

3.  **State (The Data DTOs):** These are simple, serializable data classes holding all of an agent's attributes.
    - Examples: `FirmStateDTO`, `HouseholdSnapshotDTO`.
    - Functionality currently provided by `BaseAgent` will be broken out into composable components that are part of the agent's state or body.
        - **Wallet/Finances:** The existing `Wallet` class will be composed directly by the agent's Body.
        - **Inventory:** An `InventoryManager` component will be created to handle inventory and quality logic, implementing the `IInventoryHandler` interface. It will be composed by the agent's Body.

## Consequences

#### **Pros**
*   **Superior Testability**: Brain components can be tested in complete isolation by passing them mock State DTOs. The Body can be tested by providing mock Brains. This resolves the core issue of mocking inherited `BaseAgent` properties.
*   **Enhanced Flexibility**: Brains can be swapped out easily (e.g., substituting a simple rule-based engine for a complex AI-driven one) without altering the agent's Body.
*   **Clear Separation of Concerns**: The distinction between state (data), logic (brains), and orchestration (body) becomes explicit and enforced by the architecture.
*   **Architectural Consistency**: Formalizes the pattern that `Firm` and `Household` have already organically evolved towards, reducing architectural debt and code drift.

#### **Cons**
*   **Refactoring Effort**: All agents inheriting from `BaseAgent` must be modified. `BaseAgent` itself must be dismantled.
*   **Increased Boilerplate**: Agent classes will need to explicitly delegate calls to their composed components (e.g., `self.wallet.deposit(amount)`) instead of inheriting the methods directly. This is a reasonable trade-off for the gains in testability and clarity.
*   **Breaking Changes**: Any code that relies on `isinstance(agent, BaseAgent)` will break and must be updated to use more specific interface checks (duck typing or Protocol-based).

## Phased Migration Plan

1.  **Phase 1: Create Core Components**
    *   Solidify the standalone `Wallet` as the standard financial component.
    *   Create a new `InventoryManager` class that implements `IInventoryHandler` and encapsulates all inventory logic (add, remove, quality tracking) currently in `BaseAgent` and `Firm`/`Household` overrides.

2.  **Phase 2: Refactor `Household`**
    *   Remove `BaseAgent` from `Household`'s inheritance chain.
    *   In `Household.__init__`, compose the `Wallet` and the new `InventoryManager`.
    *   Update methods like `add_item`, `deposit`, `withdraw`, `get_quantity` to delegate directly to these components instead of using `super()`. The internal `_econ_state` DTO will hold the data managed by these components.

3.  **Phase 3: Refactor `Firm`**
    *   Perform the same refactoring for the `Firm` class, removing `BaseAgent` inheritance and composing the `Wallet` and `InventoryManager`.
    *   This is the opportune moment to remove the deprecated compatibility proxies (`Firm.hr`, `Firm.finance`) identified in `TDL-PH9-2`, updating any remaining call sites.

4.  **Phase 4: Deprecate `BaseAgent`**
    *   Once all agents are migrated, the `simulation/base_agent.py` file can be safely deleted.
    *   A final pass will be made to remove any lingering type hints or checks referencing `BaseAgent`.