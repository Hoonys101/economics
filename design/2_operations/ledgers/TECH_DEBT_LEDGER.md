---

### TDL-PH9-2: Post-Orchestrator Refactor Debt (RESOLVED)

*   ** 현상 (Phenomenon) **: The `Firm` refactor to an Orchestrator-Engine pattern introduced necessary but temporary code constructs.
*   ** 기술 부채 (Technical Debt) **:
    1.  ~~**Compatibility Proxies**~~: [RESOLVED PH10] Removed `Firm.hr` and `Firm.finance` proxies.
    2.  ~~**Inheritance Friction**~~: [RESOLVED PH9.3] `Firm` and `Household` no longer inherit from `BaseAgent`.
    3.  ~~**DTO Inconsistency**~~: [RESOLVED PH9.3] Standardized `OrderDTO`.
*   ** 해결 방안 (Resolution) **:
    -   [DONE] Remove `BaseAgent` inheritance from core agents.
    -   [DONE] Remove `HRProxy` and `FinanceProxy`.
    -   [DONE] Standardize the `OrderDTO` interface across the codebase.

---

### TDL-PH9-3: Composition & Purity Aftermath (RESOLVED)

*   ** 현상 (Phenomenon) **: Final structural cleanup identified remaining hardcoded logic and transitionary proxies.
*   ** 기술 부채 (Technical Debt) **:
    1.  ~~**Hardcoded Tax Rates**~~: [RESOLVED PH10] Linked to `FiscalPolicyDTO` from Government.
    2.  ~~**Legacy Flow Access**~~: [RESOLVED PH10] Analytics normalized to use `AgentTickAnalyticsDTO`.
    3.  ~~**Abstraction Leaks**~~: [RESOLVED PH9.3] Engines now use ContextDTOs/Protocols.
*   ** 해결 방안 (Resolution) **:
    -   [DONE] Bridge `FiscalPolicyDTO` to `Firm` via `generate_transactions` context.
    -   [DONE] Fully decommission `BaseAgent.py`.

---

### TDL-PH10: Post-Refactor Stabilization Debt

*   ** ID: TD-255 (Mock Fragility) **: Inheritance/composition refactor broke many legacy tests that relied on internal attribute paths (e.g., `firm.hr.employees`). New tests must use public interfaces or state DTOs.
*   ** ID: TD-256 (Dynamic State Leaks) **: `LifecycleManager` dynamically adds `is_distressed` to `FinanceState` via `hasattr`. This should be formally added to the `FinanceState` DTO.
*   ** ID: TD-257 (Engine Hardcoding) **: `FinanceEngine` has hardcoded default unit costs (5.0). Should be moved to config.
