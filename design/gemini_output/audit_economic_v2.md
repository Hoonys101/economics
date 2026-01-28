# [AUDIT-ECONOMIC-V2] Economic Integrity & Leakage Report

## 1. Discovered Leak Points (Zero-Sum Violations)

### A. Inheritance Liquidation Leak (Critical)
*   **Location**: `simulation/systems/inheritance_manager.py` (Method: `process_death`)
*   **Mechanism**:
    The `process_death` method takes a snapshot of the deceased agent's assets (`cash = deceased.assets`) at the start of execution. It then calculates `remaining_cash` based on this *initial* snapshot minus tax paid.
    However, if the agent lacks sufficient cash to pay taxes, `Liquidation` transactions are generated to sell stocks/real estate. These transactions, when executed by the `TransactionProcessor`, convert assets to cash, significantly increasing `deceased.assets`.
    The subsequent `escheatment` transaction (for agents with no heirs) uses the pre-calculated `remaining_cash` value (which ignores liquidation proceeds).
*   **Result**: The cash generated from asset liquidation (equity) remains in the deceased agent's wallet after the escheatment transaction is processed. The agent is then removed from the simulation by `LifecycleManager`, causing this residual cash to **evaporate** (exit the closed economy).
*   **Severity**: **High**. In scenarios with high mortality and asset-rich/cash-poor agents, this causes significant deflation.

### B. Lifecycle Household Liquidation Dependency
*   **Location**: `simulation/systems/lifecycle_manager.py` (Method: `_handle_agent_liquidation`)
*   **Mechanism**:
    The `LifecycleManager` relies entirely on `InheritanceManager.process_death` to handle the transfer of assets for dying households. Because `InheritanceManager` fails to sweep the post-liquidation cash (as described above), `LifecycleManager` proceeds to clear the agent (`state.agents.clear() ...`), finalizing the deletion of the un-transferred assets.
*   **Result**: Propagates the Inheritance Leak.

---

## 2. Atomicity Violation Analysis

### Transaction Processing (Goods & Tax)
*   **Location**: `simulation/systems/transaction_processor.py` (Block: `transaction_type == "goods"`)
*   **Observation**:
    The system executes the trade and tax collection as two separate, sequential steps:
    1.  `settlement.transfer(buyer, seller, trade_value)`
    2.  `government.collect_tax(tax_amount, ...)`
*   **Atomicity Check**:
    If Step 1 succeeds (assets transferred) but Step 2 fails (e.g., due to precise floating-point insufficient funds for tax *after* the trade, or system error), the tax is not collected.
*   **Zero-Sum Verification**:
    Mathematically, this is **NOT** a Zero-Sum Violation in terms of asset creation/destruction.
    *   **Scenario (Tax Fail)**: `Buyer` loses $P$. `Seller` gains $P$. `Government` gains $0$.
        *   $\Delta System = (-P) + (+P) + 0 = 0$.
    *   **Scenario (Tax Success)**: `Buyer` loses $P + T$. `Seller` gains $P$. `Government` gains $T$.
        *   $\Delta System = (-P - T) + (+P) + (+T) = 0$.
*   **Conclusion**: The system preserves zero-sum integrity even on failure, but it suffers from **Tax Leakage/Evasion** (Integrity Violation). The transaction is not atomic; goods can move without tax being paid.

---

## 3. Solutions (Pseudocode)

### A. Fix for Inheritance Leak (The "Sweep" Strategy)

Instead of calculating a fixed `remaining_cash` value based on a stale snapshot, the `InheritanceManager` should generate a special `ESCHEATMENT_SWEEP` transaction. The `TransactionProcessor` must then handle this by dynamically transferring *all* remaining assets at the moment of execution.

**In `simulation/systems/inheritance_manager.py`:**
```python
if not heirs:
    # Instead of calculating remaining_cash...
    tx = Transaction(
        buyer_id=deceased.id,
        seller_id=government.id,
        item_id="escheatment_sweep",
        quantity=1.0,
        price=0.0, # Placeholder
        transaction_type="escheatment_sweep", # New Type
        time=current_tick
    )
    transactions.append(tx)
```

**In `simulation/systems/transaction_processor.py`:**
```python
elif tx.transaction_type == "escheatment_sweep":
    # Dynamic Sweep of ALL remaining assets
    current_assets = buyer.assets
    if current_assets > 0:
        # Atomic transfer of everything left
        settlement.transfer(buyer, seller, current_assets, "escheatment_sweep")
        # Record as revenue for Government logic
        # (Assuming seller is Government)
        if hasattr(seller, "record_revenue"):
             # Mock result object or call strictly tailored method
             seller.record_revenue({
                 "success": True,
                 "amount_collected": current_assets,
                 "tax_type": "escheatment"
             })
```

### B. Fix for Transaction Atomicity (Strict Solvency Check)

Ensure the buyer has enough funds for *both* the price and the tax before moving a single penny.

**In `simulation/systems/transaction_processor.py`:**
```python
elif tx.transaction_type == "goods":
    tax_amount = trade_value * sales_tax_rate
    total_cost = trade_value + tax_amount

    # 1. Strict Solvency Pre-check
    if buyer.assets < total_cost:
        # Fail the ENTIRE transaction
        # logger.warning("Transaction aborted: Insufficient funds for Price + Tax")
        continue

    # 2. Execute Atomic-ish Sequence (Safe because we checked funds)
    # Ideally, SettlementSystem should support multi-leg transfers,
    # but this is the next best thing without refactoring the core kernel.
    transfer_success = settlement.transfer(buyer, seller, trade_value, ...)
    if transfer_success:
        # This is now almost guaranteed to succeed due to Pre-check
        tax_result = government.collect_tax(tax_amount, ...)
        if not tax_result['success']:
            # CRITICAL ERROR: Inconsistency detected despite pre-check
            logger.critical("Atomicity Violation: Tax failed after trade!")
```
