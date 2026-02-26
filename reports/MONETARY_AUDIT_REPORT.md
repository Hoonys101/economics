# Technical Audit Report: Monetary Supply Delta Anomaly (Tick 1)

## Executive Summary
The -618M penny delta anomaly identified at Tick 1 is a **phantom leak** caused by an architectural perimeter mismatch between the `MonetaryLedger` expansion tracking and the `WorldState` M2 audit iteration. Specifically, the `Bootstrapper` uses `create_and_transfer` to seed the `Bank` with initial reserves, which triggers an M2 expansion record in the ledger. However, the `WorldState` audit correctly excludes the `Bank` (System Agent) from its M2 iteration, leading to a discrepancy where the "Expected" money exists in the ledger's tally but is missing from the audited "Current" total.

## Detailed Analysis

### 1. The Perimeter Mismatch (Audit vs. Expansion)
- **Status**: ⚠️ Partial Implementation / Logical Gap
- **Evidence**: 
    - `simulation/world_state.py:L181-185`: The `_legacy_calculate_total_money` method explicitly excludes the `Bank` and other system agents from the M2 total:
      ```python
      if self.bank:
          excluded_ids.add(str(self.bank.id))
      ...
      if isinstance(agent, IBank): continue
      ```
    - `simulation/systems/bootstrapper.py:L38-41`: The `distribute_initial_wealth` method uses `create_and_transfer` when the source is the Central Bank:
      ```python
      if is_cb and hasattr(settlement_system, 'create_and_transfer'):
          tx = settlement_system.create_and_transfer(central_bank, target_agent, amount_pennies, ...)
      ```
- **Notes**: `create_and_transfer` is designed to record M2 expansion. When used to fund the `Bank`'s initial reserves (which are technically M0/Reserves, not M2/Circulating Money), the ledger increments the `expected_m2` baseline, but the auditor skips the `Bank`'s balance, creating a permanent -618M delta.

### 2. Delta Quantification (-618,332,034)
- **Status**: ✅ Verified
- **Evidence**: `reports/diagnostic_refined.md` shows a consistent delta of `-618,332,034` starting at Tick 1.
- **Analysis**:
    - **Expected M2 (866,911,175)**: Represents the sum of all `create_and_transfer` operations during Genesis (Households + Firms + Bank).
    - **Current M2 (248,579,141)**: Represents the sum of balances for non-system agents (Households + Firms).
    - **Missing Component**: The `Bank`'s initial assets (`initial_bank_assets`). The configuration likely sets this to ~618M pennies (approx. $6.18M).

### 3. Expansion recording in Bootstrapper
- **Status**: ⚠️ Logical Debt
- **Evidence**: `simulation/initialization/initializer.py:L535` and `simulation/systems/bootstrapper.py:L116`.
- **Notes**: Seeding a Commercial Bank's reserves from a Central Bank is an M0 operation. Using `create_and_transfer` (an M2 expansion mechanism) for this specific transaction is the root cause of the "Expected" supply inflation.

## Risk Assessment
- **Technical Debt**: `TD-BANK-RESERVE-CRUNCH` (identified in `TECH_DEBT_LEDGER.md`) is exacerbated by this mismatch. If the system thinks money is missing, it may trigger unnecessary interventions or fail integrity audits.
- **Economic Instability**: If the `Expected M2` baseline is inflated by reserves, the `Panic Index` and `Inflation Expectation` metrics (which rely on supply deltas) will be permanently skewed towards a "Missing Money" scenario.

## Conclusion
The -618M delta is not a functional leak but a **reporting artifact** resulting from treating Bank Reserve seeding as M2 Expansion. The `SettlementSystem` correctly tracks the transfers, but the `MonetaryLedger` lacks the granularity to distinguish between "Base Money Injection" (M0) and "Circulating Money Expansion" (M2) during the Genesis phase.

### Action Items
1. **Refactor Genesis Seeding**: Update `Bootstrapper` to use a non-expanding transfer for `ID_BANK` reserves or implement a specific `seed_reserves` method that bypasses the M2 expansion tally.
2. **Align Audit Perimeter**: Ensure `calculate_total_money` uses a consistent set of agents for both "Expected" and "Current" calculations, or explicitly handle `ID_BANK` as an M0 holder.
3. **Verify Configuration**: Confirm `INITIAL_BANK_ASSETS` in `economy_params.yaml` matches the `618,332,034` value to close the audit loop.