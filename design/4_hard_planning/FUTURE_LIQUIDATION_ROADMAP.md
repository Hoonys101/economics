File: communications/insights/spec-comprehensive-liquidation-plan.md
```markdown
# Insight Report: Comprehensive Liquidation Plan Analysis

**Date**: 2026-02-19
**Author**: Gemini-CLI (Scribe)
**Context**: Pre-planning analysis for Phase 19/20 Technical Debt Liquidation.

## 1. Architectural Insights & Debt Reconciliation

### 1.1. Ghost Constant Redundancy (`TD-CONF-GHOST-BIND`)
- **Observation**: `TECH_DEBT_HISTORY.md` records `TD-SYS-GHOST-CONSTANTS` as resolved via `ConfigProxy` (2026-02-15).
- **Analysis**: `TD-CONF-GHOST-BIND` in the active ledger appears to be a duplicate or a residual tracking item for updating *consumers* to use the new proxy.
- **Decision**: The plan treats this as a "Verify & Close" task in Wave 5, rather than a new architectural feature.

### 1.2. The "Float" Trap in Markets (`TD-MKT-FLOAT-MATCH`)
- **Risk**: The `MatchingEngine` is the last bastion of floating-point math in the core loop. Converting this to `int` (Pennies) will inevitably break 50+ unit tests that rely on specific float division outcomes (e.g., `10.5` price).
- **Strategy**: 
    - Introduce `IMatchingStrategy` with a `RoundingPolicy` (Floor, Ceil, Banker's).
    - Default to `Floor` (Market Maker keeps remainder) to ensure strictly non-negative system balance (Zero-Sum safe).
    - **Crucial**: Do not simply cast `int()`. Use `decimal.Decimal` for intermediate calculation if precision requires it, then quantize to Penny.

### 1.3. Transaction Logic Schism (`TD-PROC-TRANS-DUP`)
- **Observation**: We have `TransactionManager` (Legacy) and `TransactionProcessor` (New).
- **Insight**: The new `TransactionProcessor` must become the SSoT. The plan must explicitly deprecate and then remove `TransactionManager` after verifying zero usage via `grep`.

## 2. Strategic Clustering (Wave Approach)

To minimize context switching and merge conflicts, debts are grouped by **Domain** and **Risk**:

- **Wave 3 (Critical Integrity)**: Focus on Data & Money. If the DB schema or Market Math is wrong, nothing else matters.
- **Wave 4 (Structural)**: Focus on Lifecycle & Logic. Decomposing the God Class (`LifecycleManager`) requires a stable Data layer from Wave 3.
- **Wave 5 (Hygiene)**: Focus on UI & Config. Low risk, high polish.

## 3. Verification Evidence (Pre-computation)
- Current Test Status: **848 PASSED** (Phase 16.2).
- The Plan includes a mandatory "Regression Check" step after each Wave.

## 4. Conclusion
The path forward is clear. We prioritize **Data Integrity** (Wave 3) over **Code Aesthetics** (Wave 4). The `MatchingEngine` refactor is the highest risk item and requires the most careful testing strategy (Dual-Running).
```

File: design/3_work_artifacts/specs/spec_comprehensive_liquidation_plan.md
```markdown
# Specification: Comprehensive Technical Debt Liquidation Plan (Phase 19-20)

## 1. Introduction
This specification outlines the strategy for liquidating the remaining Technical Debt items identified in `TECH_DEBT_LEDGER.md` following the completion of Phase 18. The plan is organized into three "Waves" to ensure stability and minimize regression risk.

- **Objective**: Achieve 100% Architectural Compliance and Data Integrity.
- **Scope**: Market Engine, Database Schema, Lifecycle Orchestration, Transaction Processing, and UI/Config Hygiene.
- **Success Criteria**: 
    - All Critical/High priority debts in `TECH_DEBT_LEDGER.md` are marked Resolved.
    - Zero floating-point math in the Core Economic Loop.
    - Zero "God Class" orchestrators.

---

## 2. Wave 3: Market & Data Integrity (The "Hard Math" Wave)
**Focus**: Elimination of Floating-Point Math from Persistence and Market Logic.
**Risk**: High (Financial Integrity).

### 2.1. Market Engine Refactor (`TD-MKT-FLOAT-MATCH`)
- **Objective**: Convert `MatchingEngine` and `StockMatchingEngine` to use strict Integer Math (Pennies).
- **Changes**:
    - **Refactor**: `simulation/markets/matching_engine.py`
        - Replace `1e-09` checks with `quantity > 0` (int).
        - Replace `effective_price_dollars` (float) with `unit_price_pennies` (int).
        - Implement `RoundingPolicy` (Floor/Ceil) for price division.
    - **DTO Update**: `CanonicalOrderDTO`
        - Ensure `quantity` is strictly `int`.
        - Add `unit_price_pennies` field; deprecate `price` (float).
- **Verification**:
    - Run `tests/market/test_precision_matching.py`.
    - Verify Zero-Sum property in `test_fiscal_integrity.py` with 100,000 tick simulation.

### 2.2. Database Schema Migration (`TD-TRANS-INT-SCHEMA`)
- **Objective**: Align the Persistence Layer (`Transaction` model) with the Penny Standard.
- **Changes**:
    - **Model**: `simulation/models.py` (Transaction)
        - Add `unit_price_pennies: int`.
        - Add `total_pennies: int`.
        - Mark `price: float` as Deprecated (computed property).
    - **Migration**: Create `scripts/migrations/001_transaction_schema_int.sql` to alter table and backfill data.
- **Verification**:
    - Run `scripts/verify_housing_transaction_integrity.py`.
    - Check `percept_storm.db` schema using `sqlite3`.

### 2.3. Reporting DTO Hardening (`TD-DTO-RED-ZONE`)
- **Objective**: Ensure all Analytics and Reporting DTOs use Pennies to prevent "Display Layer" rounding errors.
- **Changes**:
    - **DTOs**: `MarketReportDTO`, `AgentStateDTO`.
    - **Service**: `ReportingService` (or equivalent) to handle Penny-to-Dollar conversion *only* at the final JSON serialization step for UI.

---

## 3. Wave 4: Structural Decomposition (The "Lifecycle" Wave)
**Focus**: Decoupling Orchestration Logic and Event-Driven Architecture.
**Risk**: Medium (Logic Complexity).

### 3.1. Lifecycle Manager Dissolution (`TD-ARCH-LIFE-GOD`)
- **Objective**: Break the `LifecycleManager` monolith into independent Systems coordinated by Events.
- **Changes**:
    - **New Components**:
        - `BirthSystem` (Independent, listens to `TickEvent`).
        - `DeathSystem` (Independent, listens to `TickEvent`).
        - `AgingSystem` (Independent, listens to `TickEvent`).
    - **Orchestrator**: `SimulationEngine` (or `TimeSystem`) emits `TickEvent` via `TelemetryExchange`.
    - **Refactor**: Remove `simulation/systems/lifecycle_manager.py`.
- **Verification**:
    - Run `tests/unit/test_lifecycle_reset.py`.
    - Verify birth/death rates match `demographics.yaml` targets.

### 3.2. Transaction Processor Unification (`TD-PROC-TRANS-DUP`)
- **Objective**: Establish `TransactionProcessor` as the Single Source of Truth for transaction execution.
- **Changes**:
    - **Deprecate**: `simulation/systems/transaction_manager.py`.
        - Add `@deprecated` warning to all methods.
        - Redirect `execute()` calls to `TransactionProcessor`.
    - **Refactor**: `TransactionProcessor`
        - Ensure it handles all logic currently in `TransactionManager` (e.g., `escheatment`, `tax`).
    - **Cleanup**: Remove `TransactionManager` in Phase 20.
- **Verification**:
    - Grep codebase for `TransactionManager` usage.
    - Run `tests/unit/test_transaction_processor.py`.

---

## 4. Wave 5: Hygiene & Cleanup (The "Polish" Wave)
**Focus**: Code Quality, Configuration, and UI.
**Risk**: Low.

### 4.1. Ghost Constant Verification (`TD-CONF-GHOST-BIND`)
- **Objective**: Verify `ConfigProxy` adoption and remove residual direct imports.
- **Action**:
    - Grep for `from config import ...` patterns.
    - Replace with `import config` and `config.VALUE` access.
    - Mark `TD-CONF-GHOST-BIND` as Closed.

### 4.2. UI DTO Purity (`TD-UI-DTO-PURITY`)
- **Objective**: Enforce Type Safety in the UI/Cockpit layer.
- **Action**:
    - Introduce `pydantic` models for all Telemetry/WebSocket messages.
    - Remove manual `dict` construction in `dashboard/services/`.

---

## 5. Execution Plan & Dependencies

| Wave | Task ID | Dependency | Est. Effort |
| :--- | :--- | :--- | :--- |
| **3** | `TD-MKT-FLOAT-MATCH` | None | High |
| **3** | `TD-TRANS-INT-SCHEMA` | `TD-MKT-FLOAT-MATCH` | Medium |
| **3** | `TD-DTO-RED-ZONE` | `TD-TRANS-INT-SCHEMA` | Low |
| **4** | `TD-ARCH-LIFE-GOD` | Wave 3 Complete | Medium |
| **4** | `TD-PROC-TRANS-DUP` | None | Medium |
| **5** | `TD-CONF-GHOST-BIND` | None | Low |
| **5** | `TD-UI-DTO-PURITY` | None | Low |

## 6. Risk Assessment
- **Critical Risk**: `TD-MKT-FLOAT-MATCH` refactor may destabilize market equilibrium if rounding bias is introduced. **Mitigation**: Use "Maker-Takes-Remainder" (Floor) policy.
- **Migration Risk**: DB Schema change requires careful handling of existing `percept_storm.db`. **Mitigation**: Backup DB before migration script execution.

## 7. Mandatory Reporting
- All findings during implementation MUST be recorded in `communications/insights/`.
- Architecture Decision Records (ADR) must be updated if `MatchingEngine` logic changes significantly.
```