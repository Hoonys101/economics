# [Insight] Tech Debt Survival Verification Audit

**Date**: 2026-02-21
**Auditor**: Gemini-CLI Protocol Validator
**Mission**: Verify survival of "Open" and "Identified" Tech Debt items from `TECH_DEBT_LEDGER.md`.

## 1. Architectural Insights & Verification Status

| ID | Status | Verdict / Evidence |
| :--- | :--- | :--- |
| **TD-ARCH-FIRM-COUP** | 🔴 **OPEN** | `self.parent` usage persists in `Household` structure (verified via design specs/grep). Firm components still tightly coupled. |
| **TD-INT-BANK-ROLLBACK** | 🟢 **RESOLVED** | `TransactionEngine` and `TransactionExecutor` now use `IFinancialEntity` protocol (`deposit`/`withdraw`) instead of `hasattr`. |
| **TD-RUNTIME-TX-HANDLER** | 🔴 **OPEN** | `bailout` and `bond_issuance` are **NOT** registered in `SimulationInitializer`. `TransactionProcessor` will likely fail or drop these types. |
| **TD-PROTO-MONETARY** | 🟢 **RESOLVED** | `MonetaryTransactionHandler` uses `isinstance(obj, IInvestor)` and `isinstance(obj, IIssuer)`. `hasattr` usage removed. |
| **TD-DEPR-STOCK-DTO** | 🟡 **PARTIAL** | `StockOrder` class removed from models (mostly), but `DeprecationWarning` persists in logs (`tests/unit/test_market_adapter.py`). Adapter is active. |
| **TD-SYS-ACCOUNTING-GAP** | 🔴 **OPEN** | `GoodsTransactionHandler` does not explicitly call `record_expense` on buyer (Firm). Only `FinancialTransactionHandler` does. |
| **TD-ARCH-FIRM-MUTATION** | 🟡 **PARTIAL** | `Firm.produce` uses DTOs, but `Firm.record_expense` passes mutable `finance_state` to `FinanceEngine`, violating strict statelessness. |
| **TD-ANALYTICS-DTO-BYPASS** | 🟢 **RESOLVED** | `AnalyticsSystem` now uses `agent.create_snapshot_dto()` (Household) and `agent.get_state_dto()` (Firm). |
| **TD-SYS-PERF-DEATH** | 🔴 **OPEN** | `DeathSystem._handle_agent_liquidation` rebuilds `state.agents` dictionary from scratch (`clear()` + `update()`), which is O(N). |
| **TD-CRIT-SYS0-MISSING** | 🔴 **OPEN** | `CentralBank` (ID 0) is created but **NOT** added to `sim.agents` map in `SimulationInitializer`. `SettlementSystem` lookup for ID 0 may fail if not handled by fallback. |
| **TD-CRIT-PM-MISSING** | 🔴 **OPEN** | `PublicManager` is created but **NOT** registered in `sim.agents`. It cannot receive funds via standard Settlement methods relying on Registry. |
| **TD-DB-SCHEMA-DRIFT** | 🔴 **OPEN** | `TransactionData` DTO expects `total_pennies`, but legacy DB schema likely misses it. Migration required. |

## 2. Regression Analysis (Existing Failures)

Analysis of `fails.txt` reveals 27 existing failures, indicating significant regression or debt in the current codebase *before* any changes:

*   **DTO Mismatch**: `TypeError: BorrowerProfileDTO.__init__() got an unexpected keyword argument 'borrower_id'` (Multiple hits). This confirms **TD-DTO-DESYNC** mentioned in `api.py` comments is active and breaking tests.
*   **Protocol Violation**: `AttributeError: 'dict' object has no attribute 'loan_id'` in `LoanMarket`. Legacy dict usage persists despite DTO mandates.
*   **Assertion Errors**: `assert 10.0 == 1000` in `TestFinanceEngine`. Likely a Float vs Int Pennies mismatch (10.0 dollars vs 1000 pennies).

## 3. Test Evidence

*   **Source**: Analyzed `test_results_final.txt` (923 Passed) and `fails.txt` (27 Failed).
*   **Conclusion**: The system is in a **mixed state**. Core logic passes (923 tests), but recent Refactors (Finance/Bank) have broken integration points (27 failures).