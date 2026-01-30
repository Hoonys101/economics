# Technical Specification: Housing System Money Leak Fix

**Target File**: `simulation/systems/housing_system.py`

## 1. Objective
Refactor `housing_system.py` to eliminate ALL direct asset modifications (`_add_assets`, `_sub_assets`) and enforce the use of `simulation.settlement_system.transfer()`.

## 2. Required Changes

### 2.1. `process_housing`: Rent Collection
- **Current**: Direct `tenant._sub_assets` and `owner._add_assets`.
- **New**:
  ```python
  success = simulation.settlement_system.transfer(tenant, owner, rent, "rent_payment", tick=simulation.time)
  if not success:
      # Trigger eviction logic
  ```

### 2.2. `process_housing`: Maintenance Cost
- **Current**: Fallback logic using `owner._sub_assets`.
- **New**:
  ```python
  simulation.settlement_system.transfer(
      owner,
      simulation.government,
      cost,
      "housing_maintenance",
      tick=simulation.time
  )
  ```

### 2.3. `process_transaction`: Housing Purchase
- **Current**:
  - `buyer._add_assets(loan_amount)` (Magic money)
  - `buyer._sub_assets` / `seller._add_assets` (Direct transfer)
- **New**:
  1.  **Loan**: Use `simulation.bank.withdraw_for_customer(buyer.id, loan_amount)`.
      - If this fails, rollback loan via `simulation.bank.void_loan`.
      - **DO NOT** use `_add_assets`.
  2.  **Purchase**:
      ```python
      success = simulation.settlement_system.transfer(
          buyer, seller, trade_value, f"purchase_unit_{unit.id}", tick=simulation.time
      )
      if not success:
          # Critical failure: Rollback loan and abort.
      ```

## 3. Constraints
- **SettlementSystem Check**: At the start of methods, check `if not simulation.settlement_system: raise RuntimeError`.
- **Zero-Sum**: Ensure no value is created or destroyed outside of the bank/tax logic.
