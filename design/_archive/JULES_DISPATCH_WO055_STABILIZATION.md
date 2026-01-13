# [WO-055 Recovery] Simulation Stability & KPI Tuning

## 1. Context & Diagnostics
- **Target:** "The Golden Age" (WO-055). Population 2x, GDP 5x.
- **Current State:** Technical blockers for firm creation (INVEST orders) are fixed. Entrepreneurship is hyper-active (over 500 firms created).
- **Core Problem:** Despite entrepreneurship, the economy is stagnant/declining (Population 0.18x). 
- **Fatal Bottlenecks:**
    1. **Money Supply Leaks:** `MONEY_SUPPLY_CHECK` shows huge negative deltas (-400k+). Money is disappearing somewhere during firm creation or death.
    2. **Bank Illiquidity:** Sudden investment booms drain bank reserves, causing `Withdrawal failed` for survivors' food money.
    3. **Parameter Imbalance:** Fertilizer and Education effects are active but not strong enough to trigger the targeted exponential growth.

## 2. Dispatch Tasks for Jules

### A. Money Supply Forensics
- **Goal:** Resolve the `MONEY_SUPPLY_CHECK` delta.
- **Hypothesis:** 
    - Check `firm_management.py`: Is `founder_household.assets -= startup_cost` correctly balanced with `firm.assets += startup_cost`?
    - Check `Simulation._handle_agent_lifecycle`: When 500+ firms close down, is their remaining capital destroyed or returned to the founder/government?
    - Check `TransactionProcessor`: Ensure `sales_tax` and `income_tax` don't destroy money (must go to Government).

### B. Central Bank Liquidity Injection
- **Goal:** Prevent "Bank Run Starvation".
- **Implementation:** 
    - Modify `simulation/engine.py` (or `Bank`): If `bank.assets` falls below a critical threshold (e.g., 50,000) AND there are pending `WITHDRAW` orders, have the `Government` or "Central Bank" inject liquidity into the Bank's reserves.
    - This is a "Lender of Last Resort" mechanism.

### C. Golden Age KPI Tuning
- **Goal:** Achieve Population > 200% and GDP > 500% in `golden_age_test.py`.
- **Action:** 
    - Tune `FERTILIZER_POP_GROWTH_BONUS` in `config.py`.
    - Increase `LEARNING_EFFICIENCY` or the `TECH_DIFFUSION` multiplier in `technology_manager.py`.
    - Run `scripts/experiments/golden_age_test.py` for 1,000 ticks and verify results.

## 3. Reference Files
- [engine.py](file:///c:/coding/economics/simulation/engine.py) (INVEST handling added)
- [ai_driven_household_engine.py](file:///c:/coding/economics/simulation/decisions/ai_driven_household_engine.py) (Survival buffer added)
- [golden_age_test.py](file:///c:/coding/economics/scripts/experiments/golden_age_test.py) (KPI script)
