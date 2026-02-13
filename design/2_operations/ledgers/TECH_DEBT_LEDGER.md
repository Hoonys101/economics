# Technical Debt Ledger (TECH_DEBT_LEDGER.md)

| ID | Module / Component | Description | Priority / Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TD-GHOST-CONSTANTS** | System | **Registry Binding**: `from config import PARAM` binds at import time, bypassing updates. | **High**: Logic Inconsistency. | Open |
| **TD-DATA-01-MOCK** | Finance | **Protocol/Mock Drift**: `ISettlementSystem` lacks `audit_total_m2`. Manual mocking in tests. | **High**: Regression Risk. | Open |
| **TD-DATA-02-ACCESSOR** | System | **Registry Bloat**: `GlobalRegistry` lacks dot-notation support; accessor logic duplicated in Telemetry. | **Medium**: Maintenance Bloat. | Open |
| **TD-DATA-03-SCALE** | analysis | **O(N) Verifier Bottleneck**: `ScenarioVerifier` iterates all agents in Phase 8 for stats. | **Medium**: Performance (Scale). | Open |
| **TD-AGENT-REGISTRY-SCALE** | System | **M2 Audit Capacity**: O(N) iteration over all agents for M2 calculation. | **Medium**: Performance (Scale). | Open |
| **TD-DTO-OVERLAP** | Finance | **DTO Schism**: Overlap between `modules/finance/api.py` and new `Government` DTOs. | **Low**: Code Duplication. | Open |
| **TD-GOV-SERVICE-FLATTEN** | Government | **Legacy Coupling**: `TaxService` still depends on `TaxationSystem` and `FiscalPolicyManager`. | **Medium**: Structural Purity. | Open |
| **TD-COCKPIT-FE** | Simulation | **Ghost Implementation**: FE missing sliders/HUD for Cockpit (Phase 11) despite BE readiness. | **Medium**: Logic usability gap. | Identified |
| **TD-STR-GOD-DECOMP** | Architecture | **Residual God Classes**: `Firm` (1276 lines) and `Household` (1042 lines) exceed 800-line limit. | **Medium**: Maintenance friction. | Open |
| **TD-ARCH-LEAK-CONTEXT** | Finance | **Abstraction Leak**: `LiquidationContext` passes agent interfaces instead of pure DTO snapshots. | **Low**: Future coupling risk. | Identified |
| **TD-ARCH-DI-SETTLE** | Architecture | **DI Timing**: `AgentRegistry` injection into `SettlementSystem` happens post-initialization. | **Low**: Initialization fragility. | Open |
| **TD-DOC-PARITY** | Documentation | **Missing Manual**: `AUDIT_PARITY.md` missing from operations manuals. | **Low**: Knowledge loss. | Identified |
| **TD-ENFORCE-NONE** | System | **Protocol Enforcement**: Lack of static/runtime guards for architectural rules. | **High**: Regression risk. | Open (Phase 15) |
| **TD-CONFIG-LEAK** | Architecture | **Encapsulation**: Direct access to `agent.config` in internal systems. | **Medium**: Coupling risk. | Open |

---
> [!NOTE]
> ✅ **Resolved Debt History**: For clarity, all resolved technical debt items and historical lessons have been moved to [TECH_DEBT_HISTORY.md](./TECH_DEBT_HISTORY.md).

---

## 📓 Implementation Lessons & Detailed Debt (Open)


---
### ID: TD-GHOST-CONSTANTS
### Title: Module-level Import Binding (Ghost Constants)
- **Symptom**: `from config import PARAM` binds the value at import time. Even if `GlobalRegistry` is updated, the locally bound `PARAM` remains stale in the importing module.
- **Risk**: Inconsistent behavior when using hot-swapping sliders in modules using old import patterns.
- **Solution**: Complete refactor to `import config` and use `config.PARAM`.

---
### ID: TD-DATA-01-MOCK
### Title: Protocol Drift in Settlement System
- **Symptom**: `ISettlementSystem` protocol is missing `audit_total_m2` and `mint_and_distribute` definitions, forcing manual mocking (without `spec`) in `CommandService` tests.
- **Risk**: Protocol violations may go undetected; high maintenance cost for tests.
- **Solution**: Standardize `ISettlementSystem` and internal implementation.

---
### ID: TD-DATA-02-ACCESSOR
### Title: Registry Accessor Logic Duplication
- **Symptom**: `GlobalRegistry` only supports single-key `get()`. `TelemetryCollector` has to implement its own recursive dot-notation resolution logic.
- **Risk**: Code duplication as other modules start needing path-based access.
- **Solution**: Move recursive accessor logic into `GlobalRegistry.get_path()`.

---
### ID: TD-ARCH-DI-SETTLE
### Title: Dependency Injection Fragility in Settlement System
- **Symptom**: `AgentRegistry` is injected into `SettlementSystem` post-initialization.
- **Risk**: Circular dependency risks during startup; fragile initialization order.
- **Solution**: Implement a proper DI container or split initialization into distinct registration phases.
- **Reported**: `review_backup_20260212_081300_Analyze_this_PR.md`

---
### ID: TD-COCKPIT-FE
### Title: Simulation Cockpit Frontend Ghost Implementations
- **Symptom**: `PROJECT_STATUS.md` marks Phase 11 (Cockpit) as completed, but `frontend/src` lacks Base Rate/Tax sliders, Command Stream Intervention UI, and "M2 Leak" header stats.
- **Solution**: Implement missing React components in `GovernmentTab.tsx`, `FinanceTab.tsx`, and Header HUD.
- **Reported**: `PROJECT_PARITY_AUDIT_REPORT_20260212.md`

---
### ID: TD-STR-GOD-DECOMP
### Title: Residual Orchestrator Bloat (Firm & Household)
- **Symptom**: `Firm` (1276 lines) and `Household` (1042 lines) remain over the 800-line limit despite engine delegation.
- **Solution**: Further extract non-core orchestrator logic (e.g., `BrandManager` in Firms, `Legacy Mixins` in Households) into dedicated service components.
- **Reported**: `STRUCTURAL_AUDIT_REPORT.md` (2026-02-12)

---
### ID: TD-ARCH-LEAK-CONTEXT
### Title: Interface-based Abstraction Leaks in Contexts
- **Symptom**: `LiquidationContext` and `FiscalContext` pass `IFinancialEntity` (Agent) instead of raw DTOs or Snapshots.
- **Solution**: Refactor these contexts to accept only Pydantic/Dataclass DTOs or specialized Services.
- **Reported**: `STRUCTURAL_AUDIT_REPORT.md` (2026-02-12)

---
### ID: TD-DOC-PARITY
### Title: Missing Operations Manual for Parity Audits
- **Symptom**: `AUDIT_PARITY.md` manual is missing from the operations directory.
- **Solution**: Restore or recreate the `AUDIT_PARITY.md` manual.
- **Reported**: `PROJECT_PARITY_AUDIT_REPORT_20260212.md`

