# Mission Integrity Fix: Insights & Technical Debt

## Overview
This mission addresses critical integrity issues in the `TransactionProcessor` and `FinanceDepartment` that violate zero-sum principles and distort economic accounting.

## Technical Debt

### 1. `FinanceDepartment` Legacy Fallbacks
- **Issue:** `pay_severance` contains a legacy fallback that directly mutates agent assets (`self.debit`, `employee.deposit`) if a `SettlementSystem` is not available.
- **Impact:** This bypasses the centralized transaction logging and verification mechanisms, potentially leading to asset drift if `SettlementSystem` logic evolves (e.g., to include fees or taxes).
- **Resolution:** Removed the fallback. The operation now fails if `SettlementSystem` is missing, enforcing the "Sacred Sequence".

### 2. `TransactionProcessor` Tax Attribution
- **Issue:** `_handle_labor_transaction` receives a single `tax_amount` which is the sum of all tax intents. It blindly subtracts this from the seller's income.
- **Impact:** If the buyer (Firm) pays a tax (e.g., payroll tax), the seller's (Worker) recorded income is reduced by that amount, even though they received the full wage (or wage minus withholding). This distorts household income statistics.
- **Resolution:** Split tax attribution into `buyer_tax_paid` and `seller_tax_paid`. Only subtract `seller_tax_paid` from seller's income.

### 3. `TransactionProcessor` Firm Expense Recording
- **Issue:**
  - Firms paying payroll taxes do not record the tax as an expense (only the gross wage).
  - Firms buying goods (e.g., raw materials) do not record the purchase as an expense at all in `_handle_goods_transaction`.
- **Impact:** Firms under-report expenses, leading to inflated `current_profit`. This causes them to pay higher dividends and taxes than they can afford, eventually leading to liquidity crises ("Cash Crunch").
- **Resolution:** Ensure `total_buyer_cost` (including taxes) is calculated and passed to `record_expense` for both labor and goods transactions.

### 4. `Government` Deprecated Methods
- **Issue:** `collect_tax` is deprecated but used by `FinanceDepartment.pay_ad_hoc_tax`.
- **Impact:** Reliance on deprecated wrappers.
- **Resolution:** Refactor `FinanceDepartment` to use `SettlementSystem` directly.

## Verification
- Reproduction script `reproduce_integrity.py` confirms the accounting errors.
- Fixes will be verified against this script.
