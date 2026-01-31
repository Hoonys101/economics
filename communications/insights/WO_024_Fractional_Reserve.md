# Insight: Fractional Reserve Banking & Auditable Credit (WO-024)

## Overview
This mission implements a compliant Fractional Reserve Banking system, replacing direct state manipulation of the money supply with an auditable, transaction-based approach. This aligns with `ARCH_TRANSACTIONS.md` and fixes integrity issues detected by `trace_leak.py`.

## Key Changes
1.  **Transactional Credit Creation/Destruction**:
    *   `Bank.grant_loan` now returns a `(LoanInfoDTO, Transaction)` tuple. The transaction records `credit_creation`.
    *   `Bank.void_loan`, `Bank.process_default`, and the newly added `Bank.terminate_loan` return a `Transaction` recording `credit_destruction`.
    *   These transactions are symbolic (Buyer=Bank/Gov, Seller=Gov/Bank) and serve as M2 audit records.

2.  **Centralized Accounting**:
    *   `Government` now includes `process_monetary_transactions` to track `credit_delta_this_tick`.
    *   `Government.get_monetary_delta` aggregates minting, burning, and credit operations for precise leak detection.

3.  **Orchestration Updates**:
    *   `Phase1_Decision` was found to ignore transactions returned by `market.place_order`. This caused `LoanMarket` transactions (and others) to be lost. This is fixed by capturing and appending them to `state.transactions`.
    *   `Phase3_Transaction` now explicitly feeds `state.transactions` to `government.process_monetary_transactions`.

## Technical Debt & Discoveries
*   **Missing `terminate_loan`**: `HousingSystem` calls `simulation.bank.terminate_loan`, but the method was missing in `Bank`. Added as part of this refactor.
*   **Lost Transactions in Phase 1**: `Phase1_Decision` logic for placing orders previously discarded returned transactions. This likely affected `LoanMarket` and potentially `OrderBookMarket` immediate fills. Fixed to ensure data integrity.
*   **HousingSystem Direct Calls**: `HousingSystem` calls `Bank` methods directly instead of going through a market or strictly decoupled interface. This remains but is patched to handle the new transactional returns.

## Verification
*   `scripts/trace_leak.py` is updated to verify that the authorized monetary delta (calculated by Government) matches the actual change in M2, confirming zero-sum integrity with fractional reserve mechanics.
