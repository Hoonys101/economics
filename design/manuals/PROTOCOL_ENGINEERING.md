# 🏗️ Protocol: Engineering & Design

This protocol defines the architectural standards and design workflows for the project.

---

## 🏛️ 1. Architectural Pillars
1.  **Zero-Sum Financial Integrity**: No money or asset can be created or destroyed without explicit QE/Tax logic.
2.  **SoC (Separation of Concerns)**:
    *   **Agent Logic**: Pure decision making (System 1/2). NO direct Market access.
    *   **Market Logic**: Order matching and transaction generation.
    *   **System Logic**: Governing the simulation loop (e.g., TickScheduler).
3.  **DTO (Data Transfer Object) Pattern**: Data must move between layers via DTO classes, never raw dictionaries.

---

## 📄 2. Technical Specification (Spec) Standards
Implementation never begins without an approved Spec.

### Required Spec Components:
- **Interfaces**: DTO and Class signatures in `api.py`.
- **Logic Flow**: Step-by-step pseudocode for the business logic.
- **Exception Handling**: Specific error cases and fallback strategies.
- **Verification Plan**: Unit tests and integration trace requirements.
- **🚨 Risk & Impact Audit**: Analysis of circular references or test regressions.

### Documentation Philosophy (Jules):
- **Code-First**: Populate specs by reading actual code, not guessing.
- **Traceability**: Cite file and line numbers (e.g., `[engine.py:L120]`) for logic sources.

---

## 🔄 3. The Sacred Sequence (Execution Loop)
All simulation logic MUST occur within these 4 phases:
1.  **Phase 1: Decisions**: Agents generate `Order` objects based on DTO Snapshots.
2.  **Phase 2: Matching**: Markets match orders and generate `Transaction` objects.
3.  **Phase 3: Transactions**: The `TransactionProcessor` executes asset transfers (Settlement).
4.  **Phase 4: Lifecycle**: Systems handle aging, depreciation, needs updates, and effects.

---

## ⚖️ 4. Validation & Quality Control
### Protocol Validation Criteria:
- **No Mock-Magic**: Do not use `MagicMock` for agents. Use `GoldenLoader` fixtures.
- **Clean Imports**: No circular dependencies.
- **Type Safety**: Mandatory Type Hints and Google Style Docstrings for all new methods.
- **Zero-Sum Check**: Mandatory `scripts/trace_leak.py` verification for every PR.
