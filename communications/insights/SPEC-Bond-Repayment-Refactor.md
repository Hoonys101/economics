# Technical Insight: Bond Repayment Refactor

## 1. Problem Phenomenon
- **Symptoms**:
  - "Dueling Ledgers" anti-pattern where `MonetaryTransactionHandler` modified `government.total_money_destroyed` directly, while `MonetaryLedger` also tracked destruction.
  - Inaccurate M2 modeling: Interest payments on bonds were being destroyed (contracting M2) instead of just transferring (neutral M2).
  - Diagnostics (`trace_leak.py`) required manual patches to account for discrepancies.

## 2. Root Cause Analysis
- **Architecture**: `MonetaryTransactionHandler` was stateful, modifying government ledger properties.
- **Logic**: `bond_repayment` was treated as a monolithic "burn" operation. The distinction between principal (which burns when paid to CB) and interest (which is income for CB and should theoretically return to economy via dividends/spending, but is definitely not destroyed) was missing.
- **Data Model**: `Transaction` object lacked structure to carry split details.

## 3. Solution Implementation Details
- **DTO**: Introduced `BondRepaymentDetailsDTO` in `modules/government/api.py`.
- **Handler**: Refactored `MonetaryTransactionHandler` to be stateless. It no longer touches `government` properties.
- **Ledger**: `MonetaryLedger` now inspects `transaction.metadata` for `BondRepaymentDetailsDTO`. It only counts `principal` as monetary destruction. Includes legacy fallback for backward compatibility.
- **Creation**: `FinanceSystem.service_debt` updated to populate the new DTO.
- **Verification**: New unit tests (`tests/unit/test_monetary_ledger_repayment.py`) verify the split and fallback logic.

## 4. Lessons Learned & Technical Debt
- **Lesson**: Money creation/destruction logic must be centralized (in `MonetaryLedger`). Handlers should only handle movement.
- **Lesson**: Transactions need rich metadata for complex economic events.
- **Tech Debt**: `Government.total_money_destroyed` property might still be referenced elsewhere in legacy code (though `MonetaryLedger` updates a dictionary, `Government` has legacy properties). Future cleanup required to fully deprecate `Government` direct ledger properties if any remain.
