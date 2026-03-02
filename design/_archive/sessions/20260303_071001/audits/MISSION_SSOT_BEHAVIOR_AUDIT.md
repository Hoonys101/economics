# Behavioral SSoT Conceptual Audit: Transaction Authority Fragmentation

## Executive Summary
The simulation currently suffers from a "Bifurcated Authority" problem: financial execution is split between **SettlementSystem** (low-level, atomic execution) and **TransactionProcessor** (high-level, intent-based dispatching). This fragmentation results in scattered side-effects (M2 updates, revenue recording) across orchestration phases, creating a high risk of state pollution and "State-Ledger Divergence."

## Detailed Analysis

### 1. Fragmentation of Execution Logic
- **Status**: ⚠️ Partial
- **Evidence**: 
    - `SettlementSystem.py:L70-85`: Maintains its own `LedgerEngine` for atomic transfers.
    - `TransactionProcessor.py:L23-35`: Implements a dispatcher with custom handlers for the same concepts (e.g., transfers, PM sales).
- **Notes**: There are two "engines" running in parallel. `SettlementSystem` is the "Execution Engine," while `TransactionProcessor` is the "Market Dispatcher." They are not unified, leading to duplicate validation logic.

### 2. Scattered Side-Effects (M2 & Monetary Ledger)
- **Status**: ⚠️ Partial
- **Evidence**:
    - `SettlementSystem.py:L514-522`: Directly calls `monetary_ledger.record_monetary_expansion/contraction` during `transfer()`.
    - `transaction.py:L43-46`: Orchestration phase calls `monetary_ledger.process_transactions(successful_txs)` separately.
    - `monetary_processing.py:L21-25`: A separate phase (4.7) exists solely to process transactions into the ledger again.
- **Notes**: This is a classic "Double-Counting Risk." M2 integrity depends on whether a transaction went through `SettlementSystem.transfer` or was processed by the `MonetaryLedger` in a phase.

### 3. Intent vs. Execution Gap
- **Status**: ❌ Missing (Unified Authority)
- **Evidence**:
    - `TransactionProcessor.py:L138-140`: Explicitly skips `money_creation` and `money_destruction`, claiming they are "handled by SettlementSystem."
    - `SettlementSystem.py:L545`: Implements `create_and_transfer` (minting) as a "God Mode" bypass that doesn't use the standard `Transaction` model flow.
- **Notes**: Financial policy (minting/burning) bypasses the `TransactionProcessor` entirely, meaning market monitors and audit logs see different "truths" depending on the entry point.

## Risk Assessment
- **State-Ledger Divergence**: If a handler in `TransactionProcessor` succeeds but the subsequent ledger update in `Phase3_Transaction` fails (or vice versa), the "Live Balance" (State) and "M2 Total" (Ledger) will drift.
- **Duct-Tape Debugging**: `TransactionProcessor.py:L186-193` contains complex "Inactive Agent Guards" that replicate logic that should be centralized in the `AccountRegistry` or `LiquidityOracle`.
- **Architectural Debt**: The "Monetary Processing" phase (4.7) is redundant if `SettlementSystem` is the SSoT for execution.

## Conclusion: Behavioral SSoT Unification Plan
To achieve "Transaction Authority," the following refactoring is required:

1.  **Consolidate to execution-time Hook**: Move all `MonetaryLedger` and `MetricsService` calls *inside* `SettlementSystem`'s atomic commit block. This ensures that if the money moves, the ledger is updated in the same transaction.
2.  **TransactionProcessor as "Intent Transformer"**: Refactor `TransactionProcessor` to be a pure mapper that converts `Transaction` DTOs into `SettlementSystem.transfer()` calls, rather than executing its own logic.
3.  **Phase Decoupling**: Remove `Phase_MonetaryProcessing` and the ledger calls in `Phase3_Transaction`. The phases should only "trigger" the `TransactionProcessor`, which in turn uses the `SettlementSystem` (the Authority).
4.  **Unified Receipt Log**: Ensure `SettlementSystem` generates a `TransactionReceipt` (Behavioral SSoT) for every transfer, whether it originated from a market, a tax event, or a central bank injection.

---

# Insight Report: wo-ssot-audit.md

```markdown
# Architectural Insight: Behavioral SSoT Audit (wo-ssot-audit)

## Executive Summary
This audit identifies significant fragmentation between `SettlementSystem` and `TransactionProcessor`. The core issue is that **Intent (Market Transactions)** and **Execution (Ledger Transfers)** are decoupled, leading to scattered side-effects and high regression risks for M2 integrity.

## Detailed Findings

### 1. [Architectural Insights]
- **Dual Engine Anti-Pattern**: Found two distinct execution paths. `SettlementSystem` uses `LedgerEngine` for direct API calls, while `TransactionProcessor` uses handlers for `Transaction` objects. This causes "Handler Drift" where market transactions and system transfers follow different validation rules.
- **Ledger double-dipping**: M2 updates are currently attempted in both `SettlementSystem.transfer` (line 514) and `Phase3_Transaction` (line 44). This creates a race condition for M2 reporting.
- **Public Manager Special Case**: The `TransactionProcessor` handles `ID_PUBLIC_MANAGER` with hardcoded logic (line 74), which should be encapsulated in a `PublicManagerSystem` or handled via the standard `AccountRegistry`.

### 2. [Regression Analysis]
- **Current State**: Existing tests rely on `Phase_MonetaryProcessing` to "catch up" the ledger. If we move ledger updates to execution-time, these tests will show "Double Accounting" unless the phases are cleaned.
- **Risk**: `test_m2_integrity.py` will likely fail if the redundant processing in `monetary_processing.py` is not removed during the implementation of the SSoT.

### 3. [Recommended Action Items]
- **Unify Engine**: Force `TransactionProcessor` handlers to call `SettlementSystem.transfer`.
- **Sink Side-Effects**: Use an `ISettlementObserver` pattern in `SettlementSystem` to handle Tax, Panic Index, and M2 updates automatically upon transfer completion.
- **Delete Phase 4.7**: `Phase_MonetaryProcessing` is identified as architectural debt and should be removed.

## Conclusion
The path to "Zero-Sum Integrity" requires `SettlementSystem` to become the sole Transaction Authority. `TransactionProcessor` must be demoted to a simple dispatcher/validator of market intents.
```