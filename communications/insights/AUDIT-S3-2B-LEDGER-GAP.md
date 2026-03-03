# AUDIT-S3-2B-LEDGER-GAP: Ledger Completeness Audit (M2 Desync Investigation)

## 1. [Architectural Insights]

This audit focuses on the completeness of the `MonetaryLedger` and its ability to track M2 money supply changes (Credit Expansion/Contraction) accurately relative to the `SettlementSystem`'s balance-based calculation.

### 1.1 M2 Definition Mismatch
A critical discrepancy exists between how `SettlementSystem` defines the M2 boundary and how `MonetaryLedger` auto-detects money supply changes.

- **SettlementSystem.get_total_m2_pennies**: Excludes `ID_SYSTEM`, `ID_CENTRAL_BANK`, `ID_ESCROW`, `ID_PUBLIC_MANAGER`, and `ID_GOVERNMENT` (defined in `NON_M2_SYSTEM_AGENT_IDS`).
- **MonetaryLedger.process_transactions**: Only auto-flags expansion/contraction for `ID_CENTRAL_BANK` and `ID_PUBLIC_MANAGER`.

**The Gap**: Transactions moving money between (`ID_GOVERNMENT`, `ID_SYSTEM`, `ID_ESCROW`) and the general public (Households/Firms) result in a change in the circulating M2 supply, but are **NOT** captured by the Ledger's internal `expected_m2_pennies` counter.

### 1.2 Missing Transaction Types
The `MonetaryLedger` fallback logic for `transaction_type` is too restrictive. It only captures:
- `credit_creation`, `money_creation`, `lender_of_last_resort` (Expansion)
- `credit_destruction`, `money_destruction` (Contraction)

**Omitted Flows**:
- **Taxation**: Public -> Government (`ID_GOVERNMENT`). Should be Contraction.
- **Subsidies/Welfare**: Government -> Public. Should be Expansion.
- **Inheritance Distribution**: System (`ID_SYSTEM`) -> Public. Should be Expansion.
- **Escrow Release/Seizure**: Escrow (`ID_ESCROW`) <-> Public.

### 1.3 Bank Deposit Desync
While M2 includes demand deposits, the `Bank` agent often directly modifies its ledger (`bank_state.deposits`) without notifying the `MonetaryLedger`. If a bank creates a deposit balance to pay for internal expenses or as a loan side-effect without a "credit_creation" transaction type, this expansion is lost to the audit trail.

## 2. [Regression Analysis]

This desync leads to "Ghost Money" anomalies where the total wealth in the system (M2 Actual) diverges from the tracked supply (M2 Expected). This makes it impossible to verify the **Zero-Sum Principle** for systemic agents.

## 3. [Test Evidence]

Inspection of `modules/finance/kernel/ledger.py` (Lines 197-202):
```python
# Expansion: System -> Public (Money Injection)
if buyer_id in [ID_CENTRAL_BANK, ID_PUBLIC_MANAGER] and seller_id not in [ID_CENTRAL_BANK, ID_PUBLIC_MANAGER]:
    is_expansion = True

# Contraction: Public -> System (Money Drain)
elif seller_id in [ID_CENTRAL_BANK, ID_PUBLIC_MANAGER] and buyer_id not in [ID_CENTRAL_BANK, ID_PUBLIC_MANAGER]:
    is_contraction = True
```
**Finding**: `ID_GOVERNMENT` (1), `ID_SYSTEM` (5), and `ID_ESCROW` (3) are missing from these conditionals.

### Recommendation Matrix
| Component | Issue | Hardening Point |
| :--- | :--- | :--- |
| `MonetaryLedger` | Incomplete System ID set | Expand `is_expansion / is_contraction` checks to use the full `NON_M2_SYSTEM_AGENT_IDS` set. |
| `MonetaryLedger` | Rigid Type Filtering | Add `tax`, `subsidy`, `inheritance`, and `dividend` to the auto-detection types. |
| `SettlementSystem` | Duplicate Detection Logic | Centralize the expansion/contraction detection logic into a single utility used by both components. |
| `Bank` | Invisible Liability Mutation | Ensure ALL deposit adjustments generate a `Transaction` observable by the ledger. |
