I will write the mandatory insight report to `communications/insights/phase23-debt-liquidation-planning.md` and then the comprehensive liquidation roadmap to `design/3_work_artifacts/specs/PHASE23_LIQUIDATION_ROADMAP.md`.

I will generate the content for the required insight report and the liquidation roadmap.

**File: `communications/insights/phase23-debt-liquidation-planning.md`**

```markdown
# Phase 23 Debt Liquidation Strategy: The "Safety Net First" Doctrine

## 1. Executive Summary
The comprehensive audit of `TECH_DEBT_LEDGER.md` alongside `ARCH_SEQUENCING.md` reveals a critical dependency chain that dictates our liquidation strategy. We cannot safely address the high-value architectural debts (Firm Coupling, Float Corruption) because our safety net (Tests) has drifted from the actual runtime reality.

## 2. Architectural Insights
-   **The "Mock Drift" Blockade**: `TD-TEST-TX-MOCK-LAG` and `TD-TEST-LIFE-STALE` mean our current tests are verifying a version of the system that no longer exists (pre-Sequence-Refactor). Any attempt to refactor the Firm (`TD-ARCH-FIRM-COUP`) or Settlement (`TD-CRIT-FLOAT-CORE`) without fixing this first will result in false positives or unmanageable regression noise.
-   **The "Penny Standard" Imperative**: The `TD-CRIT-FLOAT-CORE` violation is not just a math error; it's a systemic integrity failure. `SettlementSystem` must be converted to `int` immediately after test stabilization to ensure M&A and dividend logic doesn't leak value.
-   **The "Stateful Firm" Reality**: We acknowledge the "Pragmatic Shift" in `ARCH_AGENTS.md` but reject the circular dependency it introduced. The roadmap prioritizes breaking the `self.parent` cycle by enforcing the SEO (Stateless Engine) pattern, but only *after* the core financial logic is solidified.

## 3. Strategic Decision: Serialization
We will execute in strict phases:
1.  **Stabilize**: Re-align Test Mocks & Lifecycle Assumptions.
2.  **Standardize**: Enforce the Penny Standard (Int) & Missing Handlers.
3.  **Refactor**: Decouple Firm Departments & Optimize AI.

## 4. Test Verification Plan
(To be executed by the implementing agents)
```python
# Verification template for Mission 1 (Test Repair)
import pytest
from tests.mocks import MockTransactionParticipant

def test_mock_protocol_adherence():
    mock = MockTransactionParticipant()
    assert isinstance(mock, ITransactionParticipant)
    assert not hasattr(mock, 'non_compliant_method')
```
```

**File: `design/3_work_artifacts/specs/PHASE23_LIQUIDATION_ROADMAP.md`**

```markdown
# Phase 23 Technical Debt Liquidation Roadmap

## 1. Overview
This roadmap orchestrates the resolution of critical technical debt identified in `TECH_DEBT_LEDGER.md`. The primary objective is to restore architectural integrity (SEO Pattern, Penny Standard) and testing reliability.

**Strategy**: `Safety Net Repair` -> `Core Integrity` -> `Architectural Refactoring` -> `Optimization`.

---

## 2. Phase 1: Operation "Safety Net" (Test Infrastructure)
**Objective**: Restore trust in the test suite by aligning mocks and lifecycle assumptions with `ARCH_SEQUENCING.md`.
**Priority**: Critical (Blocking Phase 2 & 3).

### Mission 1.1: Transaction Mock Alignment
-   **Target Debts**: `TD-TEST-TX-MOCK-LAG`, `TD-TEST-TAX-DEPR`
-   **Scope**:
    -   Refactor `tests/mocks/` to strictly implement `ITransactionParticipant` protocol.
    -   Remove deprecated `collect_tax` calls; replace with `TaxationHandler` verification.
    -   **Constraint**: Use `isinstance(mock, Protocol)` assertions.

### Mission 1.2: Lifecycle & Cockpit Hygiene
-   **Target Debts**: `TD-TEST-LIFE-STALE`, `TD-TEST-COCKPIT-MOCK`
-   **Scope**:
    -   Update `test_engine.py` to reflect `Phase_Bankruptcy` -> `Phase2_Matching` sequence.
    -   Replace `system_command_queue` usage with `CockpitOrchestrator` methods.
    -   **Constraint**: Verify `_drain_and_sync_state` is called in test harnesses.

---

## 3. Phase 2: Operation "Penny Perfect" (Financial Core)
**Objective**: Enforce Zero-Sum integrity and runtime stability.
**Prerequisite**: Phase 1 Complete.

### Mission 2.1: The Integer Migration (Penny Standard)
-   **Target Debts**: `TD-CRIT-FLOAT-CORE`, `TD-INT-BANK-ROLLBACK`
-   **Scope**:
    -   Refactor `SettlementSystem` to use `int` exclusively.
    -   Implement `BankTransactionHandler` using strict Protocols (remove `hasattr`).
    -   **Validation**: `test_settlement_index.py` must pass with 0.0000 tolerance.

### Mission 2.2: Runtime Handler Registration
-   **Target Debts**: `TD-RUNTIME-TX-HANDLER`, `TD-PROTO-MONETARY`
-   **Scope**:
    -   Register `bailout` and `bond_issuance` in `TransactionFactory`.
    -   Ensure `MonetaryTransactionHandler` adheres to `IMonetaryPolicy` protocol.

---

## 4. Phase 3: Operation "Surgical Separation" (Architecture)
**Objective**: Break circular dependencies and enforce the SEO pattern.
**Prerequisite**: Phase 2 Complete.

### Mission 3.1: Firm Department Decoupling
-   **Target Debts**: `TD-ARCH-FIRM-COUP`
-   **Scope**:
    -   **Refactor**: Extract logic from `HRDepartment`, `FinanceDepartment` into stateless Engines (`HREngine`, `FinanceEngine`).
    -   **Remove**: `self.parent` references. Pass `FirmStateDTO` to engines instead.
    -   **Pattern**: Strict SEO (Stateless Engine & Orchestrator).

### Mission 3.2: State & Config Hygiene
-   **Target Debts**: `TD-ARCH-GOV-MISMATCH`, `TD-CONF-GHOST-BIND`, `TD-ARCH-DI-SETTLE`
-   **Scope**:
    -   Standardize `WorldState.government` (Singleton vs List).
    -   Implement `DynamicConfig` proxy to solve import-time binding.
    -   Fix `AgentRegistry` injection timing in `SettlementSystem`.

---

## 5. Phase 4: Operation "Fine Tuning" (Optimization & DX)
**Objective**: Improve simulation fidelity and developer experience.
**Prerequisite**: Non-blocking, can run parallel to Phase 3.

### Mission 4.1: AI & Logic Refinement
-   **Target Debts**: `TD-AI-DEBT-AWARE`, `TD-ECON-WAR-STIMULUS`, `TD-LIFECYCLE-STALE`
-   **Scope**:
    -   Add `current_debt_ratio` to AI input DTOs.
    -   Implement `ScrubbingPhase` in `AgentLifecycleManager` to purge dead agent IDs.
    -   Tune Stimulus thresholds to prevent masking of wage issues.

### Mission 4.2: Interface & DTO Standardization
-   **Target Debts**: `TD-UI-DTO-PURITY`, `TD-DEPR-STOCK-DTO`, `TD-DX-AUTO-CRYSTAL`
-   **Scope**:
    -   Migrate UI telemetry to `pydantic` models.
    -   Replace `StockOrder` with `CanonicalOrderDTO`.
    -   Automate Manifest registration script.

---

## 6. Execution Plan & Assignments

| Phase | Mission | Estimated Effort | Parallelizable? |
| :--- | :--- | :--- | :--- |
| **P1** | 1.1 Transaction Mocks | Small | Yes |
| **P1** | 1.2 Lifecycle Tests | Medium | Yes |
| **P2** | 2.1 Integer Migration | **High** | No (Core Lock) |
| **P2** | 2.2 Handlers | Small | Yes |
| **P3** | 3.1 Firm Decoupling | **High** | No (Complex Refactor) |
| **P3** | 3.2 State Hygiene | Medium | Yes |
| **P4** | 4.1 AI & Logic | Medium | Yes |
| **P4** | 4.2 Interface & DX | Small | Yes |

**Exit Criteria**:
-   All Critical/High debts in `TECH_DEBT_LEDGER.md` marked as `Resolved`.
-   `pytest` passes with 100% coverage on new/refactored modules.
-   `Zero-Sum` Audit confirms no value leaks.
```