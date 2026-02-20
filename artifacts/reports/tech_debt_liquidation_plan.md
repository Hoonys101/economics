File: communications/insights/debt-liquidation-plan.md
```markdown
# 🛡️ Architectural Insight: Debt Liquidation Strategy

## 1. Architectural Insights & Decision Matrix
The analysis of `TECH_DEBT_LEDGER.md` reveals a clear dichotomy in the codebase's instability: **Structural Coupling** (The `Firm` God-Class) vs. **Systemic Fragility** (Financial Protocols and Injection timing). 

### Key Decisions:
1.  **Protocol-First, Structure-Second**: We cannot refactor the massive `Firm` class (`TD-ARCH-FIRM-COUP`) while the underlying transaction protocols (`TD-PROTO-MONETARY`) are brittle. If we change the Firm's structure first, we risk breaking transaction handlers that rely on the old structure's implicit attributes. Therefore, **Wave 1** focuses exclusively on "hardening the floor" (Protocols, Accounting, Settlement) before we move the furniture (Firm Refactor) in **Wave 2**.
2.  **Parallelization by Domain Isolation**:
    - **System vs. Market**: `SettlementSystem` and `DeathSystem` (System Domain) can be refactored simultaneously with `StockMarket` (Market Domain) and `Government` (Policy Domain) without file conflicts.
    - **Strict Isolation of Firm Refactor**: The `Firm` refactor is designated as a "Blocker Mission" in Wave 2. No other mission should touch `modules/firm` during this period to avoid merge hell.
3.  **The "Penny" Standard**: While not explicitly a single ticket, the `TD-SYS-ACCOUNTING-GAP` and `TD-PROTO-MONETARY` fixes are grouped to enforce the Integer/Penny standard across the transaction boundary.

## 2. Regression Risk Analysis
*   **High Risk**: `TD-ARCH-DI-SETTLE` (Dependency Injection). Changing how the Registry is injected into the Settlement System affects the `Initialization` phase.
    *   *Mitigation*: The plan requires a dedicated "Boot Sequence Test" before merging.
*   **High Risk**: `TD-ARCH-FIRM-COUP` (Firm/Department decoupling). This will break every test that instantiates a `Firm`.
    *   *Mitigation*: We will use the `GoldenLoader` to generate DTO-based fixtures and slowly replace the `Firm` class instantiation in tests.

## 3. Test Evidence (Planning Phase)
*   **Status**: Planning Phase (No Code Executed).
*   **Verification Strategy**: Each Wave includes a "Verification Gate". Wave 1 requires 100% pass on `tests/test_system/` and `tests/test_finance/`. Wave 2 requires 100% pass on `tests/test_firm/`.
```

File: design/3_work_artifacts/plans/DEBT_LIQUIDATION_SCHEDULE.md
```markdown
# 📉 Technical Debt Liquidation Schedule

## 📋 Executive Summary
This document outlines the strategic execution plan to liquidate 100% of the items currently listed in `TECH_DEBT_LEDGER.md`. The plan is divided into **3 Waves**, designed to maximize parallel execution while eliminating file conflicts.

**Goal**: Transform the codebase from a "Coupled Prototype" to a "Protocol-Driven Platform" by 2026-Q2.

---

## 🌊 Wave 1: Foundation & Integrity (The "Hard Floor")
**Objective**: Stabilize the financial core, enforce protocols, and fix dependency injection cycles. Structural refactoring of Agents is forbidden in this phase.

### 🚀 Mission 1.1: Financial Protocol Enforcement
*   **Focus**: `modules/system/transaction_*.py`, `modules/finance/bank.py`, `modules/system/accounting.py`
*   **Debts Targeted**:
    *   `TD-PROTO-MONETARY` (Low): Replace `hasattr` with `ITransactionParticipant` Protocol.
    *   `TD-INT-BANK-ROLLBACK` (Low): Implement proper rollback interface.
    *   `TD-SYS-ACCOUNTING-GAP` (Medium): Fix buyer expense tracking in accounting.
*   **Deliverables**: `IInvestor` and `IPropertyOwner` protocols fully implemented; `AccountingSystem` capturing dual-sided ledgers.

### 🚀 Mission 1.2: System Lifecycle & Dependency Hygiene
*   **Focus**: `modules/system/settlement_system.py`, `modules/system/death_system.py`
*   **Debts Targeted**:
    *   `TD-ARCH-DI-SETTLE` (Low): Fix post-init injection of `AgentRegistry`.
    *   `TD-SYS-PERF-DEATH` (Low): Optimize Agent removal (remove O(N) rebuild).
    *   `TD-LIFECYCLE-STALE` (Medium): Scrub `inter_tick_queue` on death.
*   **Deliverables**: Factory-based injection for Settlement; Optimized `DeathSystem`.

### 🏁 Wave 1 Verification Gate
- [ ] `pytest tests/test_system` passes 100%.
- [ ] `pytest tests/test_finance` passes 100%.
- [ ] No circular imports detected in `modules/system`.

---

## 🌊 Wave 2: Structural Decoupling (The "Heavy Lift")
**Objective**: Break the `Firm` God-Class and clean up peripheral domains. Mission 2.1 is complex and requires strict SEO pattern adherence.

### 🚀 Mission 2.1: Firm Architecture Overhaul (SEO Pattern)
*   **Focus**: `modules/firm/**/*.py`
*   **Debts Targeted**:
    *   `TD-ARCH-FIRM-COUP` (High): Remove `self.parent` from Departments. Inject Dependencies via Method calls or DTOs.
    *   `TD-ARCH-FIRM-MUTATION` (Medium): Refactor `BrandEngine` and `SalesEngine` to return `ResultDTOs` instead of mutating state.
*   **Deliverables**: Independent `Department` classes; Pure `FirmEngines`.

### 🚀 Mission 2.2: Market & Policy Refinement
*   **Focus**: `modules/market/*`, `modules/government/*`
*   **Debts Targeted**:
    *   `TD-DEPR-STOCK-DTO` (Low): Remove `StockOrder` legacy code.
    *   `TD-MARKET-STRING-PARSE` (Low): Use Tuple IDs or DTOs for Stock Keys.
    *   `TD-ECON-WAR-STIMULUS` (Medium): Implement progressive taxation logic.
*   **Deliverables**: `CanonicalOrderDTO` standardized; Fiscal policy masking removed.

### 🏁 Wave 2 Verification Gate
- [ ] `pytest tests/test_firm` passes 100%.
- [ ] `Firm` class lines of code reduced by >20% (Logic moved to Engines).
- [ ] All `Department` classes act as DTO holders or Orchestrators, not Logic Engines.

---

## 🌊 Wave 3: Operations, DX & Polish
**Objective**: Finalize boundaries, clean up UI/DX, and close the "Ghost" configuration issues.

### 🚀 Mission 3.1: Operational & Analytics Purity
*   **Focus**: `modules/system/analytics_system.py`, `dashboard/**/*`
*   **Debts Targeted**:
    *   `TD-ANALYTICS-DTO-BYPASS` (Low): Ensure Analytics reads from `SnapshotDTO`, not Agents.
    *   `TD-UI-DTO-PURITY` (Medium): Enforce Pydantic Models for UI Telemetry.
*   **Deliverables**: Immutable Analytics pipeline; Typed Frontend API.

### 🚀 Mission 3.2: Developer Experience & Config
*   **Focus**: `core/registry.py`, `config/*`
*   **Debts Targeted**:
    *   `TD-DX-AUTO-CRYSTAL` (Medium): Auto-discovery/registration decorator for Missions.
    *   `TD-CONF-GHOST-BIND` (Medium): Implement `ConfigProxy` for runtime tuning.
*   **Deliverables**: Zero-touch Mission registration; Hot-swappable configuration.

### 🏁 Wave 3 Verification Gate
- [ ] Full E2E Simulation run (`main.py`) completes 100 ticks without warning logs.
- [ ] Dashboard displays correct telemetry without manual casting.
- [ ] `TECH_DEBT_LEDGER.md` is empty.

---

## 📅 Execution Timeline (Estimated)
*   **Wave 1**: 3 Sessions (Focus: Stability)
*   **Wave 2**: 4 Sessions (Focus: Architecture)
*   **Wave 3**: 2 Sessions (Focus: Cleanup)
```