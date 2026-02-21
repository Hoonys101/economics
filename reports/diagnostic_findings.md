# Insight Report: Diagnostic Log Analysis & Architecture Audit

## Executive Summary
Analysis of `diagnostic_refined.md` reveals a **critical systemic failure** in the monetary injection and liquidation pipelines. The simulation is suffering from a "Liquidity Asphyxiation" event because the primary sources of liquidity (Central Bank and Public Manager) are **invisible** to the Settlement System. This prevents money from entering the economy and assets from being legally liquidated, leading to a cascade of `SETTLEMENT_FAIL` errors and "Zombie Firm" states.

## Detailed Analysis

### 1. The "Invisible Hand" Bug (Central Bank Registration)
- **Status**: ❌ **CRITICAL FAILURE**
- **Symptom**: Repeated `SETTLEMENT_FAIL | Engine Error: Source account does not exist: 0` logs.
- **Root Cause**: 
  - `ID_CENTRAL_BANK` is defined as `0` in `modules/system/constants.py`.
  - In `simulation/initialization/initializer.py`, `sim.central_bank` is instantiated but **never added** to `sim.agents` or the `AgentRegistry`.
  - The `SettlementSystem`'s `TransactionEngine` relies on the Registry to lookup account holders. Since Agent 0 is missing, all "Mint" and "OMO" operations fail validation.
- **Impact**: The economy starts with `M0` (initial minting) but cannot expand. Any attempt to inject liquidity fails, causing a deflationary spiral.

### 2. The "Broke Liquidator" (Public Manager)
- **Status**: ❌ **FUNCTIONAL FAILURE**
- **Symptom**: `LIQUIDATION_ASSET_SALE_FAIL | PublicManager failed to pay...` coupled with `Insufficient funds` errors.
- **Root Cause**:
  1.  **Registration Gap**: Like the Central Bank, `sim.public_manager` is created but likely not registered in `sim.agents` with a valid ID, making it unreachable for standard settlements.
  2.  **Insolvency**: The Public Manager attempts to buy assets (Inventory/Capital) from bankrupt firms (`Firm 120-123`) using cash it does not have. The system design (`ARCH_TRANSACTIONS.md`) implies "Escheatment" (transfer to state), but the implementation attempts a "Sale" (Exchange). Without a distinct "Mint-to-Buy" capability or massive initial reserves, the Public Manager cannot afford the assets of a failed major firm.
- **Impact**: Firms linger in `ZOMBIE` state or close without proper asset redistribution. Value is destroyed (`total_liquidation_losses`) rather than recycled.

### 3. Database Schema Drift (Migration Failure)
- **Status**: ⚠️ **DATA INTEGRITY RISK**
- **Symptom**: `Error saving transactions batch: table transactions has no column named total_pennies`.
- **Root Cause**: The Python code has been updated to support the Integer-based `total_pennies` field (adhering to `ARCH_TRANSACTIONS.md`), but the SQLite database file (`test.db` / `percept_storm.db`) persists with the legacy schema. `CREATE TABLE IF NOT EXISTS` does not auto-migrate existing tables.
- **Impact**: Transaction history is lost. Post-simulation auditing (`trace_leak.py`) will fail or produce empty results.

### 4. Floating Point "Ghost" Values
- **Status**: ⚠️ **ARCHITECTURAL DEBT**
- **Observation**: Logs show `FIRE_SALE ... at 7.50`.
- **Evidence**: `simulation/decisions/ai_driven_firm_engine.py:L128` converts this to `price_pennies=750` for the actual Order.
- **Verdict**: The *settlement* logic appears safe (using pennies), but the *decision* logic and *logging* still rely heavily on floats. This creates a cognitive dissonance in debugging and potential for rounding errors before the integer conversion boundary.

## Recommended Remediation Plan

### Immediate Fixes (Code & Data)
1.  **Register System Agents**: 
    - Update `SimulationInitializer.build_simulation()` to explicitly add `sim.central_bank` and `sim.public_manager` to the `sim.agents` dictionary before `AgentRegistry` synchronization.
2.  **Fund the Liquidator**:
    - **Option A (Preferred)**: Grant `PublicManager` the `IMonetaryAuthority` capability to "Mint" cash specifically for asset recovery (or infinite overdraft via `allows_overdraft` property in `FinancialEntityAdapter`).
    - **Option B**: Inject a massive initial endowment (e.g., 1 Trillion pennies) to `PublicManager` during Genesis.
3.  **Database Migration**:
    - Add a startup check in `DBManager`: If `transactions` table exists but lacks `total_pennies`, drop and recreate, or execute `ALTER TABLE`. Alternatively, delete old DB files in the CI/CD pipeline.

### Architectural Corrections
1.  **Formalize System IDs**: Ensure `ID_SYSTEM`, `ID_CENTRAL_BANK`, and `PublicManager.id` are reserved, constant, and guaranteed to exist in the `AgentRegistry` at tick 0.
2.  **Enforce Integer Decisioning**: Refactor `FireSale` and `StockMarket` logic to calculate limits and prices in pennies natively, removing the float-to-int conversion layer which risks off-by-one errors.

## Test Doctor Diagnosis
If `scripts/test_doctor.py` were run against the current state:
1. **Failing Module**: `tests/integration/test_liquidation_waterfall.py` (Likely passing locally only due to mocked components not reflecting the missing registry issue).
2. **Error**: `InvalidAccountError: Source account does not exist: 0`
3. **Diagnosis**: System Agents (CentralBank, PublicManager) missing from global AgentRegistry.

## Conclusion
The simulation is mathematically sound in theory but structurally disconnected in practice. The "Plumbing" (SettlementSystem) works, but the "Pipes" (Agent Registry) are not connected to the main water sources (Central Bank). Re-connecting these agents will likely resolve the vast majority of `SETTLEMENT_FAIL` errors.