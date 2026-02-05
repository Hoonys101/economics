# Mission Report: TD-033 & TD-034 Fix (Multi-Currency Liquidation & Bank Profit Integrity)

## 1. Problem Phenomenon

### TD-033: Foreign Asset Loss on Liquidation
*   **Symptom**: When a firm is liquidated, any assets held in foreign currencies (non-DEFAULT_CURRENCY) are silently destroyed/ignored. Only the primary currency (USD) balance is returned for distribution to creditors and shareholders.
*   **Impact**: Violates the zero-sum principle for foreign currencies. Causes deflationary leaks in foreign currency supply upon bankruptcy.

### TD-034: Bank Profit Absorption Logic (M2 Gap)
*   **Symptom**: There is a persistent divergence between the "Expected M2 Delta" (calculated by `MonetaryLedger`) and the "Actual M2" (calculated by `EconomicIndicatorTracker`).
*   **Detail**: `MonetaryLedger` classifies `bank_profit_remittance`, `loan_interest`, and `deposit_interest` as Expansion/Contraction events. However, `EconomicIndicatorTracker` calculates M2 as the sum of *all* wallets (Households + Firms + Bank + Government) plus Deposits.
*   **Impact**:
    *   Agent -> Bank (Interest): Ledger says Contraction. Actual M2 (Sum of Wallets) is unchanged (Transfer).
    *   Bank -> Agent (Deposit Interest): Ledger says Expansion. Actual M2 is unchanged (Transfer).
    *   Bank -> Gov (Profit Remittance): Ledger says Expansion. Actual M2 is unchanged (Transfer).
    *   This leads to a reporting gap where the Ledger reports net creation/destruction of money that does not actually change the total money stock in the system.

## 2. Root Cause Analysis

### TD-033
*   **Code Location**: `simulation/firms.py` -> `Firm.liquidate_assets`.
*   **Cause**: The method returns `float`, explicitly extracting only `DEFAULT_CURRENCY` (`self.finance.balance.get(DEFAULT_CURRENCY, 0.0)`).
*   **Constraint**: `LiquidationManager` was designed assuming single-currency liquidation waterfalls.

### TD-034
*   **Code Location**: `modules/government/components/monetary_ledger.py`.
*   **Cause**: The Ledger defines "Money Supply" implicitly as "Money in Private Circulation", excluding Bank/Gov. However, the system's SSoT for M2 (`EconomicIndicatorTracker`) includes Bank and Gov wallets in M0.
*   **Conflict**: Transfers between "Private" (Agents) and "System" (Bank/Gov) are treated as supply changes by the Ledger, but are neutral transfers within the M2 aggregate defined by the Tracker.

## 3. Solution Implementation Details

### Fix for TD-033 (Liquidation)
1.  **Refactor `Firm.liquidate_assets`**: Change return signature to `Dict[CurrencyCode, float]` to return the full asset portfolio.
2.  **Update `LiquidationManager`**:
    *   Accept asset dictionary.
    *   Use `DEFAULT_CURRENCY` portion for prioritizing debt repayment (Tiers 1-4).
    *   Distribute any remaining `DEFAULT_CURRENCY` and **all** foreign currency assets to Tier 5 (Shareholders/Equity) pro-rata.

### Fix for TD-034 (Bank Profit M2 Integrity)
1.  **Refactor `MonetaryLedger`**:
    *   Remove `bank_profit_remittance`, `loan_interest`, and `deposit_interest` from `is_expansion` / `is_contraction` logic.
    *   Retain `credit_creation` (Loan Origination) and `credit_destruction` (Principal Repayment) as the true drivers of M2 change (Deposit creation/destruction).
    *   Retain `money_creation` / `money_destruction` (Minting/Burning) as M0 drivers.

## 4. Lessons Learned & Technical Debt

*   **Metric Definition SSoT**: Different parts of the system (Ledger vs. Tracker) had different implicit definitions of "Money Supply". SSoT must be enforced centrally.
*   **Type Blindness**: The `float` return type in `liquidate_assets` was a legacy artifact that hid multi-currency complexity. Strict typing (`Dict[CurrencyCode, float]`) catches these leaks.
*   **Remaining Debt**:
    *   `SettlementSystem`'s seamless payment logic (Bank overdraft) is still primarily single-currency.
    *   Liquidation currently does not *convert* foreign assets to pay domestic debt; it only distributes them to equity holders. A future "Forex Liquidation" phase might be needed if foreign assets are required to cover domestic senior debt.
