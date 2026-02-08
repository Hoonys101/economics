# Monetary Leakage Audit Report

## Executive Summary
The systemic monetary leak is primarily caused by two critical flaws. The most significant and persistent source is a rounding error in the `handle_inheritance` function within the `DemographicManager`, which systematically destroys fractional currency. A secondary, more catastrophic cause is the lack of true atomicity in the `SettlementSystem.transfer` method, allowing funds to be withdrawn but not deposited during certain error conditions.

## Detailed Analysis

### 1. Inheritance Distribution Rounding Error
- **Status**: ❌ Confirmed Bug
- **Evidence**: `simulation\systems\demographic_manager.py:L336`
- **Notes**: The logic to distribute a deceased agent's estate to their heirs contains a critical flaw.
  ```python
  # L336
  share = math.floor((net_estate / len(heirs)) * 100) / 100.0
  ```
  The use of `math.floor` truncates each heir's share to the lowest cent. While subsequent logic (`L340-L343`) attempts to grant the remainder to the last heir, this complex approach is highly susceptible to floating-point inaccuracies, especially during the subtraction `net_estate - distributed`. Any precision lost here is permanently removed from the money supply. This aligns with the `TD-159` entry in the technical debt ledger regarding "Legacy Inheritance Redundancy" and its potential for leaks.

### 2. Non-Atomic Fund Transfers
- **Status**: ❌ Confirmed Bug
- **Evidence**: `simulation\systems\settlement_system.py:L128-L148`
- **Notes**: The core `transfer` function is not atomic. It performs the debit and credit operations sequentially within a `try...except` block.
  ```python
  # L129
  try:
      debit_agent.withdraw(amount)
      credit_agent.deposit(amount)
      ...
  except Exception as e:
      # ...
  ```
  If `debit_agent.withdraw(amount)` succeeds but `credit_agent.deposit(amount)` fails for any unexpected reason (`Exception as e`), the function returns `None` and logs the error, but it **does not roll back the withdrawal**. The money is successfully removed from the `debit_agent` but never reaches the `credit_agent`, causing it to vanish from the simulation.

### 3. Agent Liquidation (Bankruptcy)
- **Status**: ✅ Implemented Safely
- **Evidence**: `simulation\systems\settlement_system.py:L31-L51`
- **Notes**: The `record_liquidation` method correctly calculates the net value destruction (`loss_amount = inventory_value + capital_value - recovered_cash`) and adds it to a tracker. This method is for accounting purposes and does not perform any asset transfers itself; therefore, it is not a source of monetary leaks.

### 4. Birth-Related Asset Transfers
- **Status**: ✅ Implemented Safely
- **Evidence**: `simulation\systems\demographic_manager.py:L228-L232`
- **Notes**: The "birth gift" from a parent to a child is handled via a call to `settlement.transfer()`. The integrity of this process is dependent on the `SettlementSystem`, but the implementation within the `DemographicManager` is correct.

## Risk Assessment
- **High / Critical**: The inheritance rounding error represents a small but constant "monetary leak" that occurs with every death that involves multiple heirs. Over a long simulation, these small leaks accumulate into the significant M2 drift observed.
- **Medium / High**: The non-atomic transfer failure is a more acute risk. While it may occur less frequently, each failure can result in a large, sudden loss of money, explaining potential sharp drops in the money supply.
- **Informational**: The technical debt ledger (`TD-160`) also notes a "Transaction-Tax Atomicity Failure". While not directly observed in the provided code, this indicates a pattern of non-atomic operations that is likely a contributing factor to leaks in other parts of the system (e.g., market transactions with sales tax).

## Conclusion
The systemic monetary leak is not from a single source but from a combination of design flaws. **The primary culprit for the steady drift is the rounding error in `demographic_manager.handle_inheritance`**. Intermittent large drops can be attributed to the atomicity failure in `SettlementSystem.transfer`.

**Action Items:**
1.  **Immediate Fix**: Refactor the inheritance logic to use a remainder-less distribution method. Calculate all shares, sum them, find the difference from the original `net_estate`, and add that difference to the last heir's share to guarantee zero loss.
2.  **Immediate Fix**: Implement a rollback mechanism (or a two-phase commit) in `SettlementSystem.transfer` to ensure that if the credit operation fails, the debit operation is reversed.