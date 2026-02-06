# Project TODO: Phase 15 - Systemic Hardening & Refactoring

> This task list is generated from a full-system audit of architectural documents and the technical debt ledger. It prioritizes tasks based on their impact on economic stability and system integrity. All tasks must be executed with full awareness of the new **"Execute-Sync"** loop and the immutability of the stateful `Firm` component architecture.

---

## 🎯 Cluster 1: Systemic Integrity & Economic Stability (Urgent)
*Issues that directly threaten the validity of the economic simulation.*

-   [x] **[TD-257] Fix M2 Money Supply Drift:**
    -   **Description**: Investigate and resolve the residual 1.6% drift in the M2 money supply. (Resolved: 0.0000% leakage achieved).
    -   **Source**: `TECH_DEBT_LEDGER.md`
    -   **Status**: DONE ✅

-   [ ] **[TD-256] Implement Inventory Abstraction:**
    -   **Description**: Refactor inventory management to use a strict protocol (`IInventoryHandler`).
    -   **Source**: `TECH_DEBT_LEDGER.md`
    -   **Impact**: High.

-   [x] **[TD-254] Eliminate Settlement Abstraction Leaks:**
    -   **Description**: Remove `hasattr` (Resolved in Phase 6).
    -   **Status**: DONE ✅

-   [ ] **[TD-258] Remove Manual Transaction Injections:**

-   [ ] **[TD-258] Remove Manual Transaction Injections:**
    -   **Description**: Audit and refactor all instances where transactions are injected directly into the `WorldState`, bypassing the standard `Transaction` pipeline (e.g., in `Saga` handlers). All state changes must go through the formal, trackable pipeline.
    -   **Source**: `TECH_DEBT_LEDGER.md`, `[AUTO-AUDIT FINDINGS]`
    -   **Impact**: High. Guarantees that all economic activity is logged and accounted for, preventing "shadow" transactions that corrupt economic indicators.

-   [ ] **[TD-259] Unify Asset Type Handling in AI Training:**
    -   **Description**: Refactor the AI training data pipelines to handle all asset types (e.g., `dict` for currency, `float` for others) through a single, unified interface to eliminate redundant logic.
    -   **Source**: `TECH_DEBT_LEDGER.md`
    -   **Impact**: Medium. Simplifies AI model code and reduces the risk of bugs from inconsistent data types.

---

## 🏛️ Cluster 2: Architectural Refactoring & Debt Reduction (High)
*Issues that create maintenance overhead, increase cognitive load, and heighten the risk of future bugs.*

-   [ ] **[TD-253] Decompose `SettlementSystem` God Class:**
    -   **Description**: Begin the strategic decomposition of the 785-line `SettlementSystem` class. The first step should be to isolate distinct responsibilities (e.g., Saga Orchestration, Tax Collection, Debt Processing) into separate, smaller components as outlined in the `ARCH_SEQUENCING.md` decompositions.
    -   **Source**: `TECH_DEBT_LEDGER.md`, `[AUTO-AUDIT FINDINGS]`
    -   **Impact**: High. Reduces complexity, improves testability, and lowers the risk of cascading failures.

-   [ ] **[Constraint] Update Test Suite for "Execute-Sync" Loop:**
    -   **Description**: Audit and update all system and integration tests that rely on the old "end-of-tick" state synchronization model. Tests must now validate state *after each phase* to align with the new `ARCH_SEQUENCING.md` reality.
    -   **Source**: `[AUTO-AUDIT FINDINGS]`
    -   **Impact**: Critical. Without this, the test suite provides a false sense of security and cannot be trusted.

-   [ ] **[TD-037] Align Firm Agent with Stateless Architecture:**
    -   **Description**: While a full refactor is out of scope, begin documenting the specific dependencies and interactions within the stateful `Firm` components (`HRDepartment`, `FinanceDepartment`). Create a clear map of the implicit call graph to manage complexity, even if it cannot yet be eliminated.
    -   **Source**: `TECH_DEBT_LEDGER.md`, `ARCH_AGENTS.md`
    -   **Impact**: Medium. Provides a clear guide for developers to work within the existing constraints safely.

---

## 🔬 Cluster 3: Observability & Analytics (Medium)
*Gaps in logging and monitoring that prevent root cause analysis of economic anomalies.*

-   [ ] **[TD-038] Instrument Observability "Blindspots":**
    -   **Description**: Add `ThoughtProbe` logging to the key decision points currently missing instrumentation: `decide_labor` (Household), `decide_pricing` (Firm), and `match_orders` (Market). Ensure callers pre-process data to match the "dumb" logger's required schema.
    -   **Source**: `ARCH_OBSERVABILITY_THOUGHTSTREAM.md`, `TECH_DEBT_LEDGER.md`, `[AUTO-AUDIT FINDINGS]`
    -   **Impact**: High. Unlocks the ability to debug agent behavior and market failures, which is the primary goal of the "Glass Box" philosophy.

---

## 🚀 Cluster 4: Future Features & Evolution (Low)
*Items from the project roadmap that represent new functionality.*

-   [ ] **[Phase 14-3] Implement Interest Mechanics:**
    -   **Description**: Design and implement the banking system's ability to generate interest on deposits via a fractional reserve and lending mechanism.
    -   **Source**: `design/2_operations/manuals/future_roadmap.md`
    -   **Impact**: Feature Enhancement. Introduces a new, passive form of capital income.

-   [ ] **[Phase 14-4] Implement Capital Gains (Stock Market):**
    -   **Description**: Design and implement a stock exchange with an order book to allow agents to trade ownership of firms, realizing capital gains.
    -   **Source**: `design/2_operations/manuals/future_roadmap.md`
    -   **Impact**: Feature Enhancement. Completes the final stage of capital income and introduces speculative markets.
