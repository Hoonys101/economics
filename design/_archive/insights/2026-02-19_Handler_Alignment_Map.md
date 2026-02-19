# Technical Report: Fiscal & Monetary Transaction Handler Alignment Audit

## Executive Summary
This audit evaluated the alignment between transaction generation in the fiscal/monetary systems and their registration in the `TransactionProcessor`. While core handlers for QE/QT and tax are implemented, a critical gap was identified regarding **bailout** transactions and **bond issuance** types. The previously reported debt regarding `bond_interest` (`TD-RUNTIME-TX-HANDLER`) appears addressed in code but requires verification.

## Detailed Analysis

### 1. Transaction Type & Handler Mapping
- **Status**: ⚠️ Partial
- **Evidence**: `simulation/initialization/initializer.py:L305-340`
- **Findings**:
    - **MonetaryHandler**: Correctly handles `lender_of_last_resort`, `asset_liquidation`, `bond_purchase`, `omo_purchase`, `bond_repayment`, `omo_sale`, and `bond_interest`.
    - **FinancialHandler**: Correctly handles `interest_payment`, `dividend`, `tax`, `deposit/withdrawal`, and `bank_profit_remittance`.
    - **GovernmentSpendingHandler**: Handles `infrastructure_spending`, `welfare`, and `marketing`.
    - **Missing Registration**: `bailout` and `bond_issuance` (defined in `modules/government/dtos.py`) are not registered in the initializer.

### 2. Implementation Discrepancies
- **Requirement**: Identify mismatches between engine output and handler registration.
- **Findings**:
    - **`bond_interest`**: `TECH_DEBT_LEDGER.md` (TD-RUNTIME-TX-HANDLER) marks this as "Identified/Missing," but `initializer.py:L316` shows it is now registered.
    - **`bailout`**: `modules/government/dtos.py:L128` defines `bailout_results`, but no "bailout" handler exists in `initializer.py`.
    - **`bond_repayment` Logic**: `monetary_handler.py:L78-89` correctly implements QT (money destruction), but relies on `hasattr(context.government, "total_money_destroyed")`, which violates the **Protocol Purity** guardrail (should use a proper `IMonetaryLedger` or `ICentralBank` interface).

### 3. Handler Allocation Guidelines
To maintain **Zero-Sum Integrity** and **Determinism**, transaction types should be allocated as follows:

| Handler Category | Transaction Scope | Logic Impact |
| :--- | :--- | :--- |
| **Monetary** | CB <-> Banks/Gov | **Non-Zero-Sum**: Minting/Burning (QE/QT). |
| **Financial** | Agent <-> Agent | **Zero-Sum**: Wealth transfer (Dividends, Peer Interest). |
| **Government** | Gov -> Public | **Zero-Sum**: Spending from existing Treasury assets. |
| **Fiscal (Tax)** | Agent -> Gov | **Atomic**: Complex settlement involving liability clearing. |

## Risk Assessment
1.  **Runtime Failure (Bailouts)**: The absence of a registered `bailout` handler will cause the `TransactionProcessor` to fail when the Fiscal Engine attempts to save a distressed firm.
2.  **Protocol Violation**: The use of `hasattr` in `monetary_handler.py` (L81, L86) for tracking money supply is a "Technical Debt" (`TD-INT-BANK-ROLLBACK` style) that makes the system fragile to object refactoring.
3.  **Bond Type Ambiguity**: `bond_purchase` is registered, but the DTOs suggest a `bond_issuance` phase which is unhandled.

## Conclusion
The infrastructure for fiscal and monetary operations is 85% aligned. The primary action items are the registration of the `bailout` handler (likely to `FinancialTransactionHandler` or a new `EmergencyHandler`) and refactoring `MonetaryTransactionHandler` to use explicit Protocols instead of `hasattr`.

---
**Verified Transaction Types in Initializer:**
- `goods`, `labor`, `wage`, `research_labor` (Trade)
- `stock`, `asset_transfer`, `housing` (Assets)
- `interest_payment`, `loan_interest`, `deposit_interest`, `dividend`, `tax` (Finance)
- `bond_purchase`, `bond_repayment`, `bond_interest` (Monetary)
- `infrastructure_spending`, `welfare` (Spending)
- `emergency_buy` (Emergency)