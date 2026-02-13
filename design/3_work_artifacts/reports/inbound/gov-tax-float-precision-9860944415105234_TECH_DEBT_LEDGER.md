# Tech Debt Ledger: Stateless Financial Engines

## Enforcing Zero-Sum Integrity in Stateless Financial Engines

### Phenomenon
Initial refactoring to stateless engines resulted in money leaks, as engine functions only performed single-entry state updates (e.g., debiting a payer without crediting a payee). Specifically, `DebtServicingEngine` deducted interest from borrower deposits but failed to credit the Bank, causing money to vanish from the economy (deflationary leak). `LiquidationEngine` wrote off loan assets without reducing Bank equity, violating the accounting identity `Assets = Liabilities + Equity`.

### Root Cause
The design did not explicitly enforce that every state-modifying engine function must perform a complete double-entry update on the state DTO it receives. The DTO structure (`BankStateDTO`) initially lacked an explicit equity field (`retained_earnings`), leading to ambiguity about where "profits" should go.

### Solution
1.  **Explicit Equity Tracking**: Added `retained_earnings` to `BankStateDTO` to track the bank's net worth.
2.  **Double-Entry Updates**:
    *   **Interest Payment**: Debit Borrower Deposit, Credit Bank Retained Earnings.
    *   **Loan Write-off**: Credit Loan Asset (Reduce Principal), Debit Bank Retained Earnings (Loss).
3.  **Verification**: Integrated `ZeroSumVerifier` into unit tests to programmatically check the `updated_ledger` after every engine operation.