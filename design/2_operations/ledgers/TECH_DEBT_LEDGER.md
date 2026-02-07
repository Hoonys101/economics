---

### TDL-PH9-2: Post-Orchestrator Refactor Debt

*   ** 현상 (Phenomenon) **: The `Firm` refactor to an Orchestrator-Engine pattern introduced necessary but temporary code constructs.
*   ** 기술 부채 (Technical Debt) **:
    1.  **Compatibility Proxies**: `Firm.hr` and `Firm.finance` properties were added as proxies to prevent breaking external callers. They should be deprecated and removed once all call sites are updated to use the new state/engine architecture.
    2.  **Inheritance Friction**: Unit testing the refactored `Firm` highlighted difficulties in mocking properties from `BaseAgent`. This suggests that the project's inheritance-based agent design may be inferior to a Composition-based (e.g., Strategy Pattern) approach for long-term testability and flexibility.
    3.  **DTO Inconsistency**: `OrderDTO` has an ambiguous `order_type` property which is an alias for `side`. This should be standardized to avoid confusion.
*   ** 해결 방안 (Resolution) **:
    -   Create follow-up tasks to refactor agent code that relies on the deprecated proxies.
    -   Initiate an architectural review (ADR) to evaluate moving from an inheritance to a composition model for core agents.
    -   Standardize the `OrderDTO` interface across the codebase.

---
