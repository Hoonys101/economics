# Technical Audit: WO-AUDIT-HOUSEHOLD-SURVIVAL

## Executive Summary
The household sector is currently experiencing a **Liquidity Extinction Event**. Audit of `diagnostic_refined.md` and `household_ai.py` reveals that households hit a 0-cash state as early as Tick 3, triggering a "Consumption Trap" where AI Maslow Gating is active but physically impossible to satisfy due to insolvency. Furthermore, a massive **Money Supply Leak** (Delta ~11M by Tick 60) indicates a breach of Zero-Sum Integrity, where "Ghost Money" exists in the system but is not accessible to the labor-providing household sector.

## Detailed Analysis

### 1. Maslow Hierarchy vs Market (Liquidity vs Decision)
- **Status**: ⚠️ Partial (Decision Gating exists, but Liquidity is the primary blocker)
- **Evidence**: 
    - `household_ai.py:L140-162`: Implements **Maslow Gating**. If `survival_need > MASLOW_SURVIVAL_THRESHOLD` (50.0), non-survival consumption aggressiveness is forced to 0.0.
    - `reports\diagnostic_refined.md:L4-14`: Shows multiple `SETTLEMENT_FAIL` logs with `Cash: 0, Req: 800`.
- **Diagnosis**: The "Consumption Trap" is not a failure of the AI to recognize needs; it is a **Liquidity Death Spiral**. Even when the AI prioritizes survival goods, the household lacks the `balance_pennies` to clear the transaction. The market appears to have goods (Firms are trying to sell), but households cannot bridge the gap between `expected_wage` and `Cash: 0`.

### 2. Wealth Redistribution (The Wealth Gap)
- **Status**: ❌ Integrity Breach (Money Leak)
- **Evidence**: 
    - `config\defaults.py:L114`: `INITIAL_MONEY_SUPPLY` is 10,000,000 pennies.
    - `reports\diagnostic_refined.md:L13-14, L110`: 
        - **Tick 3**: Delta = 499,697.56
        - **Tick 60**: Delta = 11,085,067.46
- **Analysis**: The system is creating "Magic Money" at an exponential rate. By Tick 60, the actual money supply is **2.4x higher** than expected. Despite this surplus, households remain at `Cash: 0`, suggesting this "Ghost Money" is trapped in firm-to-firm transactions, inventory valuation errors, or settlement leaks, effectively starving the labor sector while the macro-indicators show growth.

### 3. Safety Net (Welfare Failure)
- **Status**: ❌ Missing (Regime Conflict)
- **Evidence**: 
    - `config\defaults.py:L487-495`: `INCOME_TAX_RATE = 0.0` and `CORPORATE_TAX_RATE = 0.0` (Laissez-Faire Mode).
    - `config\defaults.py:L575`: `FISCAL_MODEL = "MIXED"`.
- **Diagnosis**: The `Safety Net` defined in `Phase 4` (Welfare/Stimulus) is functionally dead because the government has **zero revenue streams** under the current Laissez-Faire settings. Without taxes, the treasury cannot fund the `UNEMPLOYMENT_BENEFIT_RATIO` (0.8), leaving households to die as soon as their initial liquidity (`INITIAL_HOUSEHOLD_ASSETS_MEAN`) is exhausted through uncompensated consumption.

## Risk Assessment
- **Zero-Sum Integrity Violation**: The growing Delta in `MONEY_SUPPLY_CHECK` is the single greatest risk to simulation validity. It suggests that `Wallet.add/subtract` or the `Registry` is failing to balance transfers.
- **Supply Shock**: `reports\diagnostic_refined.md:L66-70` shows firms (121, 122, 124) closing down due to "Consecutive Loss Turns." As firms die, the supply of `basic_food` collapses, creating a price spike that households—already at 0 cash—cannot meet.

## Conclusion
The Household Survival Trap is caused by an **unfunded stabilizer** in a **leaky economy**.
1. **The Leak**: Money is being created (Integrity Breach), distorting price signals.
2. **The Vacuum**: Laissez-Faire settings (0% tax) have disabled the government's ability to act as a lender/provider of last resort.
3. **The Outcome**: Households serve as the system's "sink," losing all liquidity to firms that eventually go bankrupt themselves because their customers (households) have died.

**Immediate Action Item**: Investigate the source of the 11M penny leak in the `Registry` or `SettlementService` before adjusting AI behaviors.