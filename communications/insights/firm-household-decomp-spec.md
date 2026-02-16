# Insight Report: God Class Decomposition Specification

**Mission**: `firm-household-decomp-spec`
**Date**: 2026-02-16
**Author**: Gemini (Scribe)
**Status**: SPECIFICATION COMPLETE

## 1. Architectural Strategy: CES Lite (Agent Shell)
We have defined a **Component-Entity-System (CES) Lite** approach to decompose the `Firm` and `Household` God Classes.
-   **Agent = Shell**: The Agent class becomes a thin wrapper (Shell) that aggregates reusable **Components**.
-   **Composition over Inheritance**: Instead of inheriting `InventoryMixin` or implementing protocols directly in the class body, the Agent holds `InventoryComponent`, `FinancialComponent`, etc.
-   **Orchestrators**: Complex procedural logic (e.g., transaction generation pipelines) is extracted into stateless **TransactionOrchestrators**.

## 2. Defined Interfaces
The following interfaces have been defined in `modules/agent_framework/api.py`:
-   `IAgentComponent`: Lifecycle management (init, reset).
-   `IInventoryComponent`: Typed inventory management (replaces dicts).
-   `IFinancialComponent`: Strict penny-based financial operations (replaces `Wallet` direct usage).
-   `ITransactionOrchestrator`: Pipeline encapsulation.

## 3. SEO Pattern Adherence
This decomposition **strictly adheres** to the Stateless Engine & Orchestrator (SEO) pattern:
-   **Engines** remain pure and stateless.
-   **Components** hold the state (Data) and provide atomic mutation methods (Logic for data integrity, e.g., "cannot remove more than you have").
-   **Agents (Orchestrators)** wire Components and Engines together. The Agent is the "Owner" of the state but delegates the "How" to Components and Engines.

## 4. Technical Debt Resolution
This specification directly addresses `TD-STR-GOD-DECOMP` by:
-   Reducing `Firm` class size by estimated 40-50% (removing boilerplate).
-   Centralizing inventory/finance logic, eliminating duplication between Firm/Household.
-   Enabling isolated unit testing of storage logic.

## 5. Next Steps
-   **Lane 3 Execution**: Proceed with Component implementation and iterative refactoring of Agents.
-   **Audit**: Verify that no circular dependencies are introduced between `simulation.agents` and `modules.agent_framework`.
