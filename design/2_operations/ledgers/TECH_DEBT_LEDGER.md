# Technical Debt Ledger (TECH_DEBT_LEDGER.md)

| ID | Module / Component | Description | Priority / Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TD-LEG-TRANS** | System | Legacy `TransactionManager` contains redundant/conflicting logic. | **Low**: Confusion & code bloat. | Pending Deletion |
| **TD-PRECISION** | Financials | Use of `float` for currency leads to precision dust/leaks over long runs. | **Medium**: Marginal zero-sum drift. | Identified (Next Priority) |
| **TD-CONFIG-MUT** | System | Scenarios directly mutate global config via `setattr`. | **Medium**: State pollution risk. | Identified (Next Priority) |
| **TD-COCKPIT-FE** | Simulation | **Ghost Implementation**: FE missing sliders/HUD for Cockpit (Phase 11) despite BE readiness. | **Medium**: Logic usability gap. | Identified |
| **TD-STR-GOD-DECOMP** | Architecture | **Residual God Classes**: `Firm` (1276 lines) and `Household` (1042 lines) exceed 800-line limit. | **Medium**: Maintenance friction. | Open |
| **TD-ARCH-LEAK-CONTEXT** | Finance | **Abstraction Leak**: `LiquidationContext` passes agent interfaces instead of pure DTO snapshots. | **Low**: Future coupling risk. | Identified |
| **TD-ARCH-DI-SETTLE** | Architecture | **DI Timing**: `AgentRegistry` injection into `SettlementSystem` happens post-initialization. | **Low**: Initialization fragility. | Open |
| **TD-DOC-PARITY** | Documentation | **Missing Manual**: `AUDIT_PARITY.md` missing from operations manuals. | **Low**: Knowledge loss. | Identified |
| **TD-ENFORCE-NONE** | System | **Protocol Enforcement**: Lack of static/runtime guards for architectural rules. | **High**: Regression risk. | Open (Phase 15) |
| **TD-CONFIG-LEAK** | Architecture | **Encapsulation**: Direct access to `agent.config` in internal systems. | **Medium**: Coupling risk. | Open |
| **TD-PH15-SEO** | Finance/Tax | **SEO Leak**: Core engines receive direct Agent handles instead of Snapshots. | **High**: Architectural Drift. | Open |

---
> [!NOTE]
> ✅ **Resolved Debt History**: For clarity, all resolved technical debt items and historical lessons have been moved to [TECH_DEBT_HISTORY.md](./TECH_DEBT_HISTORY.md).

---

## 📓 Implementation Lessons & Detailed Debt (Open)

---
### ID: TDL-031 / TD-QE-MISSING
### Title: QE Bond Issuance Logic Missing Post-Refactor
- **Date**: 2026-02-11
- **Component**: `modules.finance.system.FinanceSystem`
- **Issue**: QE Bond Issuance Logic Missing Post-Refactor
- **Description**: The `issue_treasury_bonds` function in the stateless `FinanceSystem` engine hardcodes the bond buyer as the primary commercial bank (`self.bank.id`). The original logic, which allowed the Central Bank to be the buyer under specific QE conditions (e.g., high debt-to-gdp), was lost during refactoring.
- **Impact**: The system can no longer properly simulate Quantitative Easing. Test `test_qe_bond_issuance` has a critical assertion marked as xfail to prevent build failure.
- **Reporter**: Jules (via PR #FP-INT-MIGRATION-02)
- **Status**: Open

---
### ID: TD-FIN-001
### Title: Impure Financial Engines (State Mutation)
- **Symptom**: `DebtServicingEngine`, `LiquidationEngine`, `LoanBookingEngine` directly mutate input DTOs.
- **Risk**: Breaks functional purity, creates race conditions, and complicates zero-sum verification.
- **Solution**: Refactor to `State_In -> State_Out` pattern using DTO copies.

---
### ID: TD-FIN-002
### Title: Monetary Unit Mismatch (Pennies vs Dollars)
- **Symptom**: Configs and Tax/Fiscal modules still use float dollars, requiring adapters in `TransactionManager`.
- **Risk**: Implicit unit conversions are high-friction and prone to 100x scaling errors.
- **Solution**: Complete the "Penny Standard" migration across all configurations and government modules.

---
### ID: TD-FIN-004
### Title: Missing Sovereign Risk Premium Logic
- **Symptom**: `issue_treasury_bonds` uses fixed spreads regardless of debt levels.
- **Risk**: Inability to model fiscal sustainability crises.
- **Solution**: Integrate `debt_to_gdp` based feedback loops into bond yield calculations.

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

---
### ID: TD-PH15-SEO-LEAKS
### Title: Phase 15 Residual SEO Leaks (Audit findings)
- **Symptom**: Core engines in Finance/Taxation still receive direct Agent handles instead of Snapshots/DTOs.
- **Identified Leaks**:
  1. `FinanceSystem.evaluate_solvency` (direct `firm.assets` access).
  2. `TaxService.collect_wealth_tax` (direct `IAgent` list iteration).
  3. `TaxationSystem` (direct property access on `IFinancialAgent`).
  4. Mutable DTOs in `debt_servicing_engine` and `loan_booking_engine`.
- **Status**: Open (Post-PH15)
- **Reported**: `PH15_FINAL_COMPLIANCE_AUDIT.md` (2026-02-12)
