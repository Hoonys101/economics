# Final Zero-Sum Drift Fix

## Diagnosis
A recurring positive money leak (Drift > 0) was observed in the simulation, specifically correlated with `Government.invest_infrastructure` calls. The reported drift was `+299.7760` (and `+289.2640` in some logs) for a `5000.0` investment.

### Investigation
1.  **Transaction Logic**: The existing code generated a `Transaction` of type `infrastructure` from Government to `EconomicRefluxSystem`.
2.  **Transaction Processor**: The processor handles this type via a generic fallback, calling `settlement_system.transfer`.
3.  **Reflux System**: Upon deposit, `RefluxSystem` captures the funds and later distributes them to households.
4.  **Leak Analysis**:
    *   The drift amount (`299.7760`) is remarkably specific. It does not match simple tax rates (5%, 10%) exactly on 5000.
    *   The drift represents a *creation* of money (`M2` increases more than expected).
    *   Since the `TransactionProcessor` logic involves complex conditional checks (tax, goods, labor), there is a risk that the `infrastructure` transaction is triggering a side effect (e.g., Phantom Tax, or misclassification) or that `RefluxSystem.capture` is being triggered twice in a race condition or accounting error.

## Solution
To guarantee zero-sum integrity for this critical internal transfer, we will **bypass the `TransactionProcessor`** for the infrastructure investment payment itself.

Instead of generating a `Transaction` object that might be misinterpreted, `Government.invest_infrastructure` will explicitly call `self.settlement_system.transfer()`.

### Benefits
1.  **Atomicity**: `SettlementSystem.transfer` guarantees that `Government` assets are decremented exactly by the amount `RefluxSystem` assets are incremented.
2.  **Isolation**: Prevents `TransactionProcessor` from applying sales tax or other logic to this internal transfer.
3.  **Clarity**: Explicitly models the action as a direct fiscal transfer rather than a market "trade".

## Implementation
Modify `simulation/agents/government.py`:
- In `invest_infrastructure`:
    - Check for `self.settlement_system` and `reflux_system`.
    - Execute direct transfer.
    - Omit the `infrastructure` transaction from the returned list.
    - Retain `bond` issuance transactions if needed.
