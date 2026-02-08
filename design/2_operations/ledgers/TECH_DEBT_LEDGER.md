---

### TDL-PH9-2: Post-Orchestrator Refactor Debt

*   ** 현상 (Phenomenon) **: The `Firm` refactor to an Orchestrator-Engine pattern introduced necessary but temporary code constructs.
*   ** 기술 부채 (Technical Debt) **:
    1.  ~~**Compatibility Proxies**~~: [RESOLVED PH9.3] `Firm.hr` and `Firm.finance` proxies are now isolated but still exist. They should be removed in Phase 10.
    2.  ~~**Inheritance Friction**~~: [RESOLVED PH9.3] `Firm` and `Household` no longer inherit from `BaseAgent`.
    3.  **DTO Inconsistency**: `OrderDTO` has an ambiguous `order_type` property which is an alias for `side`. This should be standardized to avoid confusion.
*   ** 해결 방안 (Resolution) **:
    -   [DONE] Remove `BaseAgent` inheritance from core agents.
    -   [TODO] Remove `HRProxy` and `FinanceProxy` once all legacy call sites are verified.
    -   Standardize the `OrderDTO` interface across the codebase.

---

### TDL-PH9-3: Composition & Purity Aftermath

*   ** 현상 (Phenomenon) **: Final structural cleanup identified remaining hardcoded logic and transitionary proxies.
*   ** 기술 부채 (Technical Debt) **:
    1.  **Hardcoded Tax Rates**: `Firm.generate_transactions` currently hardcodes income tax at 20%. This must be linked to PolicyDTO from Government.
    2.  **Legacy Flow Access**: `AnalyticsSystem` still uses `getattr` for legacy flow attributes (e.g., `labor_income_this_tick`).
    3.  ~~**Abstraction Leaks**~~: [RESOLVED PH9.3] Engines now use ContextDTOs/Protocols instead of raw agent objects.
*   ** 해결 방안 (Resolution) **:
    -   Bridge `FiscalPolicyDTO` to `Firm` via `generate_transactions` context.
    -   Fully decommission `BaseAgent.py` once all minor utility agents are confirmed independent.

---
