# Mission Spec: Taxation Mechanism Decoupling (TD-176) & Saga Pattern (TD-175)

## 1. Objective
Decouple the tax calculation and collection logic from the `TransactionProcessor` and `Government` agent, enabling a modular, extensible, and atomic taxation system. This is a critical step for **Phase 32 (Interbank Lending)** to ensure a clean financial engine.

## 2. Problem Statement
- **TD-176**: `TransactionProcessor` currently calculates taxes directly and calls `government.collect_tax()`. This creates a tight coupling where the transaction engine needs to know about tax rates, brackets, and policy specifics.
- **TD-175**: The rollback mechanism for failed transactions (especially in multipart trades like "Buyer -> Seller" + "Buyer -> Tax") is manually implemented and prone to errors.

## 3. Targeted Solution
Refactor the system to use a **TaxationSystem** (as a service) and an **Escrow-based Atomic Settlement** (Saga variation).

### 3.1 Architecture Overview

**Current Flow (Coupled)**:
1. `TransactionProcessor` sees a trade.
2. Calculates Tax (`gov.calculate_income_tax`).
3. Executes Trade (`settlement.transfer(buyer, seller)`).
4. Executes Tax (`gov.collect_tax(buyer, government)`).
   - *Risk*: If step 4 fails, step 3 is already done (Non-Atomic).

**New Flow (Decoupled & Atomic)**:
1. `TransactionProcessor` sees a trade.
2. Asks `TaxationSystem` for **Tax Intents**.
   - `intents = taxation_system.calculate_tax_for_transaction(transaction)`
3. Bundles Trade + Tax Intents into a **Settle Request**.
4. Delegates to `SettlementSystem.settle_atomic(debit_agent, credits_list)`.
   - `debit_agent` = Buyer
   - `credits_list` = `[(Seller, price), (Government, tax_amount)]`
5. `SettlementSystem` executes atomically:
   - Withdraw `total (price + tax)` from Buyer.
   - Deposit `price` to Seller.
   - Deposit `tax` to Government.
   - *If any fail, Rollback ALL.*

### 3.2 Key Components

#### A. `TaxationSystem` (New Module)
- **Role**: Pure logic component. Calculates tax obligations based on transaction details and current Government policy.
- **Location**: `modules/government/taxation/system.py`
- **Interface**:
  ```python
  class ITaxationSystem:
      def calculate_tax_intents(self, transaction: Transaction, buyer: Agent, seller: Agent) -> List[TaxIntent]:
          pass
  ```
- **TaxIntent DTO**:
  ```python
  @dataclass
  class TaxIntent:
      payer_id: int
      payee_id: int # Usually Government
      amount: float
      reason: str
  ```

#### B. `SettlementSystem.settle_atomic()` (Refactor)
- **Role**: Executes a one-to-many transfer atomically.
- **Logic**:
  1. Sum all credits to get total debit required.
  2. Attempt `debit_agent.withdraw(total)`. (Seamless Payment applies here too).
  3. Loop through credits and `deposit()`.
  4. If any deposit fails, reverse previous deposits and refund debit agent. (Saga Pattern).

## 4. Implementation Plan (For Jules)

### Step 1: Create `TaxationSystem`
- Move `calculate_income_tax`, `calculate_corporate_tax` logic from `Government` (or `TaxAgency`) to `TaxationSystem`.
- `Government` should delegate policy setting to `TaxationSystem`, but not handle calculation logic itself.

### Step 2: Implement `SettlementSystem.settle_atomic`
- Create the atomic transfer method capable of handling `1 Sender -> N Receivers`.
- Ensure strict rollback on failure.

### Step 3: Refactor `TransactionProcessor`
- Remove direct tax calculation logic.
- Inject `TaxationSystem`.
- Update `execute` loop to use the **Get Intent -> Bundle -> Settle Atomic** pattern.

### Step 4: Verify (TD-175)
- Create a test case where a trade succeeds but tax payment fails (e.g., Gov account frozen - unlikely but possible, or forced error).
- Confirm that the Seller does NOT receive money if the Tax part fails (Atomic All-or-Nothing).

## 5. Definition of Done
- [ ] `TransactionProcessor` no longer imports `Government` or calls `calculate_tax`.
- [ ] `TransactionProcessor` uses `TaxationSystem.calculate_intents`.
- [ ] `SettlementSystem` has `settle_atomic`.
- [ ] Taxes and Trades happen in a single atomic block.
- [ ] `Government.collect_tax` legacy method is deprecated/removed.
