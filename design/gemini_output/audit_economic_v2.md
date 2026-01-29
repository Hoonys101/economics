# AUDIT-ECONOMIC-V2: Economic Integrity & Leakage Report

## 1. Overview
This audit examines the `simulation/` codebase for "Zero-Sum Violations" (money creation/destruction from thin air) and atomicity issues in financial transactions. The primary focus is on identifying bypasses of the `FinanceSystem` (or `SettlementSystem`) and verifying the mathematical integrity of inheritance and tax logic.

## 2. [발견된 누출 지점 리스트] (Leak List)
The following code blocks directly modify agent assets via `_add_assets` / `_sub_assets`, bypassing the `SettlementSystem`. This bypass prevents central logging, prevents enforcing constraints (e.g., negative balances), and risks zero-sum violations if the corresponding debit/credit is not perfectly balanced manually.

### A. Critical: Housing System (Direct Ledger Bypass)
**File:** `simulation/systems/housing_system.py`
The housing system manually adjusts assets for rent, loan issuance, and property trades.
- **Lines 83, 96-97:** Rent payment.
  ```python
  tenant._sub_assets(rent)
  owner._add_assets(rent)
  ```
- **Lines 208, 223:** Mortgage/Loan issuance.
  ```python
  buyer._add_assets(loan_amount) # Money created/transferred without Bank/Settlement record?
  ```
- **Lines 231, 240:** Property Trade.
  ```python
  buyer._sub_assets(trade_value)
  seller._add_assets(trade_value)
  ```
*Risk:* If any of these operations partially fail (e.g., tenant subtracts but owner add fails), money disappears.

### B. High: Demographic Manager (Legacy Inheritance)
**File:** `simulation/systems/demographic_manager.py`
**Lines 303, 310**
- Usage: `heir._add_assets(share)` and `deceased_agent._sub_assets(...)`.
- *Conflict:* `TransactionProcessor` also handles inheritance transactions. If both systems run, double-inheritance or race conditions may occur. This direct modification also bypasses the `Transaction` log.

### C. Medium: Firm Management (Startup Capital)
**File:** `simulation/systems/firm_management.py`
**Lines 144-145**
- Usage: `founder_household._sub_assets(final_startup_cost)` / `new_firm._add_assets(final_startup_cost)`.
- *Status:* Likely zero-sum safe (manual transfer), but bypasses the `SettlementSystem` logs ("Sacred Sequence").

---

## 3. [원자성 위반 코드 블록] (Atomicity Violations)

### A. Transaction Processor: Trade & Tax Separation
**File:** `simulation/systems/transaction_processor.py`
**Lines ~60-170**

Current logic separates the trade transfer and the tax collection into two distinct operations:

```python
# 1. Trade Transfer
success = settlement.transfer(buyer, seller, trade_value, ...)

# 2. Tax Collection (Conditional on 1)
if success and tax_amount > 0:
    government.collect_tax(tax_amount, ...)
```

**Violation:**
- If `settlement.transfer` succeeds, the trade is final.
- If `government.collect_tax` fails (e.g., due to an internal error, strict solvency check, or partial insolvency if the buyer had *just* enough for the trade but not the tax), the tax is never collected.
- **Result:** The Government loses revenue (Policy Leak). The system remains physically zero-sum (Buyer keeps the tax money), but the intended economic flow is broken.

### B. Inheritance Logic Check
**File:** `simulation/systems/transaction_processor.py` (Lines ~132)
**Validation:**
- The code uses `base_amount = math.floor((total_cash / count) * 100) / 100.0`.
- It distributes `base_amount` to `N-1` heirs.
- The last heir receives `remaining_amount = total_cash - distributed_sum`.
- **Verdict:** This logic is **Mathematically Sound**. It preserves the Zero-Sum property by ensuring the residual (from flooring) is explicitly given to the last heir. No money is evaporated here, provided `SettlementSystem` can handle the float precision of `remaining_amount`.

---

## 4. [해결을 위한 슈도코드] (Pseudocode Solutions)

### A. Enforcing Atomicity in Transactions
Refactor `TransactionProcessor` and `SettlementSystem` to support "Atomic Batch Transfers".

```python
# simulation/finance/settlement_system.py

def execute_trade_with_tax(self, buyer, seller, government, trade_amount, tax_amount, reason):
    """
    Executes trade and tax atomically. Either both happen, or neither.
    """
    total_buyer_debit = trade_amount + tax_amount

    if buyer.assets < total_buyer_debit:
        return False # Fail the whole trade

    # Atomic Execution (or use database transaction)
    try:
        self.transfer(buyer, seller, trade_amount, reason)
        self.transfer(buyer, government, tax_amount, f"tax_on_{reason}")
        return True
    except Exception:
        # Rollback logic if database rollback isn't available
        # reverse_transfer(...)
        return False
```

### B. Fixing Housing System Leak (Direct -> Settlement)
Replace direct asset modification with `SettlementSystem` calls.

```python
# simulation/systems/housing_system.py

# BEFORE:
# tenant._sub_assets(rent)
# owner._add_assets(rent)

# AFTER:
success = self.settlement_system.transfer(
    sender=tenant,
    receiver=owner,
    amount=rent,
    reason="housing_rent"
)
if not success:
    # Handle eviction or debt logic
```

### C. Consolidating Inheritance
Deprecate the legacy logic in `DemographicManager` and rely solely on `InheritanceManager` generating transactions processed by `TransactionProcessor`.

```python
# simulation/systems/demographic_manager.py

# Remove or comment out direct asset modifications
# heir._add_assets(share)  <-- REMOVE
# deceased._sub_assets(...) <-- REMOVE

# Ensure InheritanceManager is generating the correct Transaction objects
# which are then processed by TransactionProcessor using the "Remainder" logic.
```
