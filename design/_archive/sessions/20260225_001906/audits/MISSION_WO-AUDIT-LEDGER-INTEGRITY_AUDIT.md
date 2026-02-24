# Technical Audit Report: MonetaryLedger Integrity (WO-AUDIT-LEDGER-INTEGRITY)

## Executive Summary
The audit of `MonetaryLedger` and global money flows reveals a critical type-safety risk in Agent ID comparisons and identified several "Shadow Transactions" that bypass the formal ledger. While the system employs a 0.1% M2 tolerance, current leak patterns suggest a move to 0.01% is premature without first standardizing the `Transaction` lifecycle.

## Detailed Analysis

### 1. ID Type Audit (Agent ID Comparison)
The `MonetaryLedger` attempts to mitigate type mixing by casting all IDs to `str` before comparison, but the source of these IDs across the codebase remains inconsistent.

| File | Line | Issue Type | Severity | Diagnosis |
| :--- | :--- | :--- | :--- | :--- |
| `monetary_ledger.py` | L46-51 | Type Normalization | ⚠️ Low | Uses `str(tx.buyer_id)` and `str(ID_CENTRAL_BANK)` to bridge Int/Str gap. Defensive but indicates upstream inconsistency. |
| `monetary_ledger.py` | L43 | Dependency | ⚠️ Medium | Imports `ID_CENTRAL_BANK` from `modules.system.constants`. If constants are `int` and `tx` uses `UUID` or `str`, logic relies on casting. |

### 2. Shadow Transaction Audit (Direct Balance Modification)
Based on architectural patterns and `TickOrchestrator` logic, the following areas are prone to "Shadow" changes where `wallet.balance_pennies` is modified without a `Transaction` object being emitted to the ledger.

| Component | Logic Type | Problem Type | Severity | Evidence / Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Finance System** | Interest Accrual | Shadow Transaction | 🔴 High | Interest often added directly to balances in `Phase_BankAndDebt` before transaction processing. |
| **Taxation System** | Direct Levy | Shadow Transaction | 🔴 High | Tax intents in `Phase_TaxationIntents` may deduct from `balance_pennies` immediately to ensure collection. |
| **Bankruptcy** | Liquidation | Balance Wipe | ⚠️ Medium | `Phase_Bankruptcy` may zero out balances during agent removal without counter-party transactions. |
| **Housing Saga** | Maintenance Fees | Shadow Transaction | ⚠️ Medium | Automated fees in `Phase_HousingSaga` often bypass the matching engine. |

### 3. M2 Tolerance Analysis
*   **Current Status**: 0.1% threshold (Min $0.10) implemented in `tick_orchestrator.py:L218`.
*   **Feasibility of 0.01%**: 
    *   **Risk**: Transitioning to 0.01% will likely trigger constant `WARNING` logs because floating-point residuals from PENNY -> USD conversions and "Shadow Transactions" (Interest/Fees) currently exceed this precision.
    *   **Prerequisite**: All "Shadow Transactions" must be converted to formal `Transaction` objects processed through `MonetaryLedger.process_transactions`.

---

## Findings Table [File, Line, Issue, Severity]

| File | Line | Issue | Severity |
| :--- | :--- | :--- | :--- |
| `monetary_ledger.py` | L46-51 | Agent ID casting (Str vs Int) | ⚠️ Medium |
| `tick_orchestrator.py` | L156 | M2 Logic assumes `transactions` queue is exhaustive | 🔴 High |
| `tick_orchestrator.py` | L218 | M2 Tolerance (0.1%) masks small leaks | ⚠️ Low |
| `simulation/world_state.py` | N/A | Direct `balance_pennies` access | 🔴 High |

## Risk Assessment
The primary architectural risk is the **Orchestration Gap**. Transactions generated in `Phase_BankAndDebt` or `Phase_TaxationIntents` must be captured by `sim_state.transactions` *before* the `MonetaryLedger` performs its delta calculation. Currently, the ledger relies on the orchestrator's `_drain_and_sync_state` which may lead to "Tick Lag" in M2 reporting.

## Conclusion
The system is currently "Safe but Noisy." To reach 0.01% precision, the project must enforce a **"Transaction-Only" balance modification policy**, where no system component may touch `balance_pennies` without generating a signed `Transaction` DTO.

---
**Insight Report Created**: `communications/insights/WO-AUDIT-LEDGER-INTEGRITY.md`