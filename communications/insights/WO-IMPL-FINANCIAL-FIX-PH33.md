# WO-IMPL-FINANCIAL-FIX-PH33: Financial Integrity & M2 SSoT Implementation Report

## 1. [Architectural Insights]

### Decoupling of M2 Tracking
The legacy implementation of M2 tracking was fragmented:
-   **Old Approach:** `TickOrchestrator` relied on `WorldState.calculate_total_money` (iterating all agents) and `Government.get_monetary_delta` (analyzing transaction logs) to estimate M2 drift. This created a split-brain problem where the "Expected" M2 was derived from Government logic, while "Actual" M2 was derived from agent iteration.
-   **New Approach:** `MonetaryLedger` (located in `modules/finance/kernel/ledger.py`) is now the strict Single Source of Truth (SSoT) for M2. It tracks `expected_m2` via explicit calls to `record_monetary_expansion` and `record_monetary_contraction`. `SettlementSystem` delegates M2 calculation to `get_total_m2_pennies`, unifying the logic.

### System Coupling Improvements
-   **TickOrchestrator**: No longer depends on `Government` internal state (`get_monetary_delta`). It simply queries `MonetaryLedger` for current vs expected M2.
-   **WorldState**: `calculate_total_money` no longer performs an O(N) iteration over all agents for M2 calculation. It delegates to `MonetaryLedger`. (Note: Debt calculation currently retains legacy iteration until fully migrated).
-   **SettlementSystem**: Now explicitly records M2 impacting events (Mint/Burn), ensuring the Ledger is always in sync with the physical money movement.

## 2. [Regression Analysis]

During implementation, several tests failed due to **Mock Drift** and **Protocol Violations**:

### Failure 1: `tests/integration/test_lifecycle_cycle.py`
-   **Issue:** `test_lifecycle_transactions_processed_in_next_tick_strong_verify` failed with `TypeError: '>' not supported between instances of 'MagicMock' and 'int'`.
-   **Cause:** The test mocked `WorldState` but did not configure the `monetary_ledger` mock. The updated `TickOrchestrator._finalize_tick` accessed `monetary_ledger.get_expected_m2_pennies()`, which returned a `MagicMock`, causing comparison failure against `int`.
-   **Fix:** Updated the test setup to explicitly mock `get_total_m2_pennies` and `get_expected_m2_pennies` to return integer values (1000).

### Failure 2: `tests/unit/test_protocol_lockdown.py`
-   **Issue:** `test_settlement_system_protocol_compliance` failed with `AssertionError`.
-   **Cause:** The `MockSettlementSystem` class used in unit tests did not implement the new methods added to `ISettlementSystem` protocol (`get_total_m2_pennies`, `get_total_circulating_cash`, `set_monetary_ledger`).
-   **Fix:** Added the missing methods to `MockSettlementSystem` to satisfy the updated protocol.

### Logic Gap Fixes (Post-Review)
-   **M2 Leak (Bond Issuance):** `FinanceSystem.issue_treasury_bonds` was updated to explicitly record M2 expansion when system agents (CB/Bank Reserves) purchase bonds from the Government (which is part of M2), preventing a divergence between Actual and Expected M2. This check now explicitly verifies the buyer is a System Agent to prevent future bugs if Households purchase bonds.
-   **Legacy Fallback Drift:** `WorldState._legacy_calculate_total_money` was updated to exclude `ID_ESCROW` and `ID_PUBLIC_MANAGER` to align with the new `SettlementSystem` logic.
-   **M2 Leak (Estate Agents):** `SettlementSystem.get_total_circulating_cash` was updated to include cash held by `EstateRegistry` agents, preventing M2 drift when agents are liquidated.

### Legacy Method Support
-   **Saga Compatibility:** `IMonetaryLedger` retains `record_credit_expansion` and `record_credit_destruction` as wrappers around the new API to prevent breaking legacy `SagaHandler` calls, although `SagaHandler` itself was also updated to use the new API for consistency.

## 3. [Test Evidence]

Full test suite execution passed successfully (1060 passed, 11 skipped).

```text
tests/unit/test_monetary_ledger_repayment.py::TestMonetaryLedgerRepayment::test_interest_is_not_destroyed PASSED [ 91%]
tests/unit/test_phase1_refactor.py::TestPhase1DecisionRefactor::test_execute_flow PASSED [ 91%]
tests/unit/test_phase1_refactor.py::TestPhase1DecisionRefactor::test_dispatch_logic PASSED [ 92%]
...
tests/unit/test_protocol_lockdown.py::test_settlement_system_protocol_compliance PASSED [ 92%]
...
tests/integration/test_lifecycle_cycle.py::TestLifecycleCycle::test_lifecycle_transactions_processed_in_next_tick_strong_verify PASSED [ 90%]
...
================= 1060 passed, 11 skipped, 1 warning in 14.12s =================
```
