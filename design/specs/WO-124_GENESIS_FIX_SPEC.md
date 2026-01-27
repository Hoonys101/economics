# Spec: WO-124 Genesis Fix (Sacred Sequence)

## 1. Overview
This specification addresses the critical **TD-115 (Tick 1 Asset Leak)** and **TD-117 (DTO Purity Regression)** issues by implementing the **"Sacred Sequence"** (Genesis Protocol) during simulation initialization.

The core problem is "Helicopter Money" introduced via direct asset mutations during initialization, which bypasses the zero-sum ledger and causes baseline supply drift.

## 2. The Sacred Sequence (Initial Protocol)

Initial initialization must follow these four steps strictly:

### Step 1: Fiat Lux (M0 Minting)
The `CentralBank` is initialized and "mints" the total initial money supply from the void. This establishes the absolute M0 baseline.
- **Action**: Add `central_bank.mint(amount)` or use `central_bank.deposit(amount)` in `SimulationInitializer.build_simulation`.
- **Source**: `CONFIG.INITIAL_MONEY_SUPPLY`.

### Step 2: Creation (Empty Pockets)
All agents (Households, Firms, Government) are created with **0.0 assets**.
- **Action**: Modify `main.py` and `DemographicManager` to ensure initial assets are 0.0 unless handed by the Central Bank.

### Step 3: Distribution (Atomic Transfer)
All initial liquidity is distributed via the `SettlementSystem`.
- **Action**: Refactor `Bootstrapper.inject_initial_liquidity` and `Bootstrapper.force_assign_workers`.
- **Logic**: 
  ```python
  # From: target._add_assets(amount)
  # To:
  settlement_system.transfer(
      debit_agent=central_bank, 
      credit_agent=target, 
      amount=amount, 
      memo="GENESIS_GRANT"
  )
  ```

### Step 4: Verification (Zero-Sum Baseline)
Immediately after distribution and before the first update, record the baseline supply.
- **Action**: `sim.world_state.baseline_money_supply = sim.world_state.calculate_total_money()`.
- **Validation**: Assert `calculate_total_money() == INITIAL_MONEY_SUPPLY`.

## 3. Implementation Details

### 3.1 `simulation/initialization/initializer.py`
- Re-order the instantiation loginc.
- Ensure `SettlementSystem`, `CentralBank`, and `Government` are ready before any agent creation.
- Perform distribution *after* agent registration in the `Registry`.

### 3.2 `simulation/systems/bootstrapper.py`
- Remove all `agent._add_assets()` or `agent.assets = X` calls.
- Inject `SettlementSystem` and `CentralBank` into the static methods or through the caller.

### 3.3 `simulation/world_state.py`
- Update `calculate_total_money` to include `CentralBank` balance if it's not already covered (Note: Central Bank starts with M0 and its balance decreases as it spends, so M2 = `Avg(Agents) + Bank_Reserves + CentralBank_Balance` should equal M0).

## 4. Verification Plan (Genesis Audit)

1. **Local Test**: Run `scripts/audit/trace_leak.py` at Tick 0 and Tick 1.
2. **Target**: `Delta: 0.000000` at both ticks.
3. **Log Check**: Look for `Initial baseline money supply established: [M0]` message.

## 5. Risk Assessment
- **Initialization Order**: Re-ordering components in `build_simulation` might break dependency chains (e.g., agents needing SettlementSystem).
- **Zero-Sum**: If CentralBank starts at 0 and goes negative, the `calculate_total_money` must correctly handle signed balances.
