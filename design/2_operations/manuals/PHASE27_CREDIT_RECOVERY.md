# Phase 27: Credit Creation Recovery Roadmap

## 🎯 Objective
Reactivate the **"Money Multiplier"** (Credit Creation) mechanism. Having secured the "Physics" layer (Zero-Sum Settlement), we now introduce "Chemistry" (Leverage) in a controlled and transparent manner.

---

## 🏗️ Architectural Requirements
1. **Authorized Minting**: Any money created via credit must be formally tracked in `SettlementSystem` as "Credit Creation".
2. **Double-Entry Integrity**: $Assets (Loans) = Liabilities (Deposits) + Equity$.
3. **Regulatory Guards**: Dynamic `LTV` (Loan-to-Value) and `DTI` (Debt-to-Income) limits enforced by the `Bank`.

---

## 📋 Action Items

### Step 1: Credit Multiplier Reactivation (Immediate)
*   [ ] **Audit Bank Balance Sheet**: Ensure the Bank can expand its liabilities (deposits) when creating assets (loans).
*   [ ] **Implement Credit Accounting**: Link `Bank.create_loan()` to `SettlementSystem.record_credit_creation()`.
*   [ ] **Status**: Not Started.

### Step 2: Regulatory Relaxation
*   [ ] **LTV/DTI Tuning**: Gradually relax the strict 1:1 reserve requirements to allow for Fractional Reserve Banking.
*   [ ] **Stress Testing**: Run simulation for 100 ticks to ensure no "Residual Evaporation" occurs under high leverage.
*   [ ] **Status**: Not Started.

### Step 3: Interest Circulation
*   [ ] **Minting vs. Transfer**: Ensure `Bank.pay_interest` is a transfer from Bank Equity to Customer Deposits, NOT a minting operation.
*   [ ] **Status**: Pending Audit.

---

## 🔭 Future Milestones (Beyond Phase 27)
*   **Phase 28**: Macro-Stability Index (Monitoring the impact of credit on GDP/Inflation).
*   **Phase 29**: Lender of Last Resort (Government/Central Bank intervention during credit crunches).
