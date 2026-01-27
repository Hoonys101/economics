# Audit Economic V2: Economic Integrity and Leak Detection

## 1. Introduction
This audit investigates the economic integrity of the simulation, focusing on "Zero-Sum" violations where assets are created or destroyed without proper accounting. The audit targets `simulation/systems/transaction_processor.py`, `inheritance_manager.py`, `lifecycle_manager.py`, and `government.py`.

## 2. Direct Asset Modification (Grep Results)
A search for direct modification of `.assets` revealed the following:

### Safe / Intentional
*   **`simulation/decisions/ai_driven_household_engine.py`**:
    *   `household.assets -= repay_amount`
    *   `household.assets = temp_assets`
    *   **Verdict**: **Safe**. This occurs within a decision engine using a DTO (`HouseholdStateDTO`). The modification is temporary for local simulation and is reverted in a `finally` block.
*   **`simulation/systems/event_system.py`**:
    *   `h.assets *= (1 + config.demand_shock_cash_injection)`
    *   `agent.assets *= (1 - config.asset_shock_reduction)`
    *   **Verdict**: **Intentional**. These are "God Mode" stress test scenarios (Hyperinflation, Deflation) designed to inject or remove liquidity exogenously.
*   **`simulation/agents/government.py`**:
    *   `_add_assets` / `_sub_assets`
    *   **Verdict**: **Safe**. Internal helper methods used by the `TransactionProcessor` or strictly controlled system components.

### Leaks / Violations
*   **`simulation/systems/lifecycle_manager.py`** (Line 169):
    *   `firm._sub_assets(firm.assets)`
    *   **Verdict**: **Leak**. During firm liquidation, if `settlement.transfer` fails or leaves residuals (e.g., floating point dust), the remaining assets are simply subtracted and added to `total_money_destroyed`. While statistically tracked, this removes circulating money from the economy without a corresponding transaction (e.g., to Government/Escheatment), effectively "evaporating" wealth.

## 3. Atomicity Violations & Logic Flaws

### A. Tax Collection Atomicity (TransactionProcessor)
In `simulation/systems/transaction_processor.py` (around line 154 for Goods):
The system calculates `trade_value` and `tax_amount`. It checks solvency for the sum, but executes the transfers sequentially.

```python
# Current Logic Structure
if settlement:
    # Step 1: Trade (Buyer -> Seller)
    success = settlement.transfer(buyer, seller, trade_value, ...)

    # Step 2: Tax (Buyer -> Government)
    if success and tax_amount > 0:
        government.collect_tax(tax_amount, ...)
```

**The Flaw**: If Step 1 succeeds (Buyer pays Seller), the Buyer's assets decrease. If Step 2 fails (e.g., due to a race condition, recalculation error, or system error in `collect_tax`), the Trade is valid, but the Tax is never collected. The Government loses revenue, and the Buyer evades tax. This is a **Policy Leak**.

### B. Inheritance Distribution (TransactionProcessor)
In `simulation/systems/transaction_processor.py` (Inheritance Logic):
The system calculates a `base_amount` to distribute to heirs and gives the remainder to the last heir.

```python
# Current Logic Structure
distributed_sum = 0.0
for i in range(count - 1):
    if settlement.transfer(buyer, heir, base_amount, ...):
        distributed_sum += base_amount
    # If transfer fails, distributed_sum does NOT increase.

# Last Heir Logic
remaining_amount = total_cash - distributed_sum
settlement.transfer(buyer, last_heir, remaining_amount, ...)
```

**The Flaw**: If an intermediate transfer fails (e.g., `heir` is invalid or system error), `distributed_sum` remains lower than expected. `remaining_amount` becomes abnormally large (containing the share of the failed transfer). The Last Heir attempts to claim this large amount.
*   If the money remained with the Deceased (Buyer), the Last Heir gets everything (Unfair Distribution).
*   If the money was deducted but not credited (Atomicity failure in `settlement`), the Last Heir transaction fails too.
*   **Verdict**: **Distribution Logic Error**. While likely Zero-Sum safe (money stays with deceased), it leads to unpredictable inheritance outcomes.

## 4. Proposed Solutions (Pseudocode)

### A. Atomic Trade Execution
Move the Trade and Tax logic into a single atomic block within `SettlementSystem` or verify execution rigorously.

```python
def execute_atomic_trade(buyer, seller, government, trade_amount, tax_amount):
    total_cost = trade_amount + tax_amount

    # 1. Pre-validation
    if buyer.assets < total_cost:
        return False # Insufficient Funds

    # 2. Execution (All or Nothing)
    try:
        # Depending on SettlementSystem capabilities, use a batch transfer
        # or optimistic locking.

        # Scenario: Batch
        transfers = [
            (buyer, seller, trade_amount),
            (buyer, government, tax_amount)
        ]
        settlement.batch_transfer(transfers)
        return True
    except TransferError:
        return False
```

### B. Safe Liquidation (Escheatment)
In `lifecycle_manager.py`, replace destruction with transfer to Government.

```python
# simulation/systems/lifecycle_manager.py

# ... inside Firm Liquidation ...
total_cash = firm.assets

# 1. Distribute to Shareholders
# ... existing logic ...

# 2. Escheat Remainder (Instead of Destroying)
remaining_assets = firm.assets
if remaining_assets > 0:
    # Transfer ALL remaining assets to Government
    if settlement:
         settlement.transfer(firm, government, remaining_assets, "liquidation_escheatment_final")
    else:
         firm.withdraw(remaining_assets)
         government.deposit(remaining_assets)

    # Now firm.assets should be 0.
    # If still > 0 due to float error, force set to 0 (destruction of dust only).
```

### C. Robust Inheritance
Calculate shares independently of transfer success.

```python
# simulation/systems/transaction_processor.py

base_amount = math.floor((total_cash / count) * 100) / 100.0
remainder_dust = total_cash - (base_amount * count)

for i, heir_id in enumerate(heir_ids):
    amount = base_amount
    if i == len(heir_ids) - 1:
        amount += remainder_dust # Only give the dust to the last heir

    # Execute Transfer independently
    settlement.transfer(buyer, heir, amount, "inheritance_distribution")

    # If this fails, the money stays with Deceased (Buyer), which is correct behavior for a failed transaction.
    # It does NOT get forwarded to the next heir or the last heir.
```