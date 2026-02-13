# Technical Debt Ledger (TECH_DEBT_LEDGER.md)

| ID | Module / Component | Description | Priority / Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TD-GHOST-CONSTANTS** | System | **Registry Binding**: `from config import PARAM` binds at import time, bypassing updates. | **High**: Logic Inconsistency. | Open |
| **TD-DATA-01-MOCK** | Finance | **Protocol/Mock Drift**: `ISettlementSystem` lacks `audit_total_m2`. Manual mocking in tests. | **High**: Regression Risk. | Open |
| **TD-DATA-02-ACCESSOR** | System | **Registry Bloat**: `GlobalRegistry` lacks dot-notation support; accessor logic duplicated in Telemetry. | **Medium**: Maintenance Bloat. | Open |
| **TD-DATA-03-SCALE** | analysis | **O(N) Verifier Bottleneck**: `ScenarioVerifier` iterates all agents in Phase 8 for stats. | **Medium**: Performance (Scale). | Open |
| **TD-AGENT-REGISTRY-SCALE** | System | **M2 Audit Capacity**: O(N) iteration over all agents for M2 calculation. | **Medium**: Performance (Scale). | Open |
| **TD-UI-01-METADATA** | Cockpit | **Registry Metadata Gap**: `RegistryService` uses hardcoded shim; `GlobalRegistry` lacks UI metadata. | **High**: UX Inconsistency. | Open |
| **TD-UI-DTO-PURITY** | Cockpit | **Manual Deserialization**: UI uses raw dicts/manual mapping for Telemetry. Lack of `dacite`-like helper. | **Medium**: Code Quality. | Open |
| **TD-UI-WS-PROD** | Cockpit | **WS Server Wiring**: Real simulation loop wiring for WebSocket server unverified. | **Medium**: Integration Risk. | Open |
| **TD-UI-PLOT-SCALE** | Cockpit | **Plotly Performance**: Large heatmap rendering in Streamlit causes UI lag. | **Low**: UX Performance. | Open |
| **TD-COCKPIT-FE** | Simulation | **Partial Readiness**: Scaffold and Visualizers done. Dynamic Controls (UI-02) pending. | **Medium**: Logic usability gap. | Partially Resolved |
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
### ID: TD-UI-01-METADATA
### Title: Missing Registry Metadata Provider
- **Symptom**: `RegistryService` in the dashboard uses hardcoded metadata because `GlobalRegistry` (FOUND-01) only stores values, not UI hints (min/max, description).
- **Risk**: Desync between engine configuration and UI controls.
- **Solution**: Extend `GlobalRegistry` or create a companion `MetadataRegistry` that provides UI schema.

---
### ID: TD-UI-DTO-PURITY
### Title: Manual DTO Mapping and Raw Dicts in UI
- **Symptom**: Dashboard often handles raw JSON dicts or uses manual loops to reconstruct `ScenarioReportDTO` from telemetry.
- **Risk**: Maintenance burden; silent failures if DTO schema changes.
- **Solution**: Adopt a serialization library (e.g., `dacite`, `pydantic`) for reliable boundary crossing.

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

