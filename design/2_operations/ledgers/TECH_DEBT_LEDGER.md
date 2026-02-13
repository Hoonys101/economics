# Technical Debt Ledger (TECH_DEBT_LEDGER.md)

| ID | Module / Component | Description | Priority / Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TD-GHOST-CONSTANTS** | System | **Registry Binding**: `from config import PARAM` binds at import time, bypassing updates. | **High**: Logic Inconsistency. | Open |
| **TD-AGENT-REGISTRY-SCALE** | System | **M2 Audit Capacity**: O(N) iteration over all agents for M2 calculation. | **Medium**: Performance (Scale). | Open |
| **TD-DTO-OVERLAP** | Finance | **DTO Schism**: Overlap between `modules/finance/api.py` and new `Government` DTOs. | **Low**: Code Duplication. | Open |
| **TD-GOV-SERVICE-FLATTEN** | Government | **Legacy Coupling**: `TaxService` still depends on `TaxationSystem` and `FiscalPolicyManager`. | **Medium**: Structural Purity. | Open |
| **TD-275** | System | **Housing ID Utility**: Duplicated `split("_")` logic across handlers. | **High**: Maintenance Fragility. | Open |
| **TD-276** | Finance | **Solvency Valuation Spec**: Ambiguity between Market vs Liquidation price for assets. | **Medium**: Logic Consistency. | Open |
| **TD-LEG-TRANS** | System | Legacy `TransactionManager` contains redundant/conflicting logic. | **Low**: Confusion & code bloat. | Pending Deletion |
| **TD-PRECISION** | Financials | Use of `float` for currency leads to precision dust/leaks over long runs. | **Medium**: Marginal zero-sum drift. | Identified (Next Priority) |
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
- **Symptom**: `from config import PARAM` binds the value at import time. Even if `GlobalRegistry` is updated, the locally bound `PARAM` remains stale.
- **Risk**: Inconsistent behavior when using hot-swapping sliders.
- **Solution**: Refactor all architectural imports to `import config` and use `config.PARAM`, or use the registry directly.

---
### ID: TD-AGENT-REGISTRY-SCALE
### Title: Agent Registry Iteration Bottleneck
- **Symptom**: M2 Audit requires O(N) iteration over all financial agents in Every Tick (Phase 8).
- **Risk**: Performance degradation as population scales (>100k agents).
- **Solution**: Implement incremental M2 tracking in `IAgentRegistry` or the `SettlementSystem`.

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

