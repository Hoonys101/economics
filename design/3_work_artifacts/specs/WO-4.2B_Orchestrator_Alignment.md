# WO-4.2B: Orchestrator Alignment & Wallet Migration

**Status**: 🔵 Drafted for Implementation (PR-Chunk #2)
**Target**: `simulation/orchestration/`, `simulation/agents/government.py`, `simulation/world_state.py`
**Goal**: Address `TD-216` by realigning the `TickOrchestrator` and completing the system-wide migration to the Wallet Abstraction Layer.

---

## 1. Executive Summary

This specification follows the implementation of the `Wallet` layer (WO-4.2A). It focuses on:
1.  **Correcting the "Sacred Sequence"** by moving governmental accounting logic out of orchestrator hooks into a dedicated `Phase_MonetaryProcessing`.
2.  **Migrating all Agent types** (`Firm`, `Government`, `Household`) to use the new `IWallet` interface for all financial transactions.
3.  **Decomposing the Government God Class** by separating fiscal spending from monetary policy tracking.

## 2. Architectural Changes

### 2.1. TickOrchestrator & Phase Alignment

The `TickOrchestrator` will no longer trigger business logic in its internal sync hooks.

1.  **Create `Phase_MonetaryProcessing`**:
    - Location: `simulation/orchestration/phases.py`
    - Resp: Call `government.monetary_ledger.process()`.
    - Position: Between Taxation Intents and Settlement.

2.  **Clean `_drain_and_sync_state`**:
    - Remove the hardcoded `government.process_monetary_transactions()` call from `simulation/orchestration/tick_orchestrator.py`.

### 2.2. Government Decomposition

Refactor `simulation/agents/government.py`:
1.  **`self.wallet: Wallet`**: For fiscal spending (taxes, welfare).
2.  **`self.monetary_ledger: MonetaryLedger`**: For tracking M2 delta, credit creation, and burning.
3.  **Encapsulation**: Replace all internal `_assets` dictionary access with `self.wallet.withdraw()` or `self.wallet.deposit()`.

### 2.3. System-Wide Migration (The Final Phase)

Ensure all remaining agents and services are migrated to the `Wallet` API:
-   **`Firm`**: Update `pay_wages` and `pay_taxes` to use `self.wallet.subtract()`.
-   **`Bank`**: Update deposit/withdrawal handlers to operate on the `Wallet` object.
-   **`CentralBank`**: Use `wallet.add()` for credit creation (which will be automatically tagged in the audit log).

## 3. Verification Plan

1.  **Zero-Sum Test**: Re-run `test_money_supply_zero_sum.py` after full migration. It must use the new `Wallet` auditing mechanism correctly.
2.  **M2 Calculation**: Verify `WorldState.calculate_total_money()` accurately sums across all agent wallets.
3.  **Sequence Check**: Assert that `MonetaryLedger.process` is called exactly once per tick within the new phase.

## 4. Risk Mitigation

-   **Phase Ordering**: Carefully monitor the sequence to ensure taxes are calculated *before* monetary deltas are finalized.
-   **Dict-to-Wallet Compatibility**: During migration, ensure that any legacy code expecting a `Dict` is handled via `wallet.get_all_balances()` to prevent immediate crashes, with a plan to remove such calls.
