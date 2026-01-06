# W-1 Spec: Phase 4.5 Interest Sensitivity (Monetary Transmission)

> **Status**: Approved by Chief Architect
> **Goal**: Connect Central Bank rates to Household decisions.

## 1. Logic Detail

### 1.1 real_rate Calculation
Real Interest Rate ($r$) is the primary signal for households.
- $i$ = `nominal_rate` (from `loan_market` data in `market_data`)
- $\pi^e$ = `expected_inflation` (average across all goods in `Household`)
- $r = i - \pi^e$

### 1.2 Substitution Effect (Savings Incentive)
Adjust consumption aggressiveness based on how far $r$ is from the neutral rate.
- Neutral Rate ($r^*$) = `config.NEUTRAL_REAL_RATE` (default 0.02)
- Sensitivity ($S$):
    - Personality Group **ANT** (`MISER`, `CONSERVATIVE`): $S = 10.0$
    - Personality Group **Grasshopper** (`STATUS_SEEKER`, `IMPULSIVE`): $S = 2.5$
- $\Delta MPC_{savings} = -1 \times S \times (r - r^*)$

### 1.3 Cashflow Channel (Debt Penalty)
Direct reduction in consumption due to interest burden on debt.
- $DSR = \frac{Daily Interest Burden}{Income Proxy}$
- $Income Proxy = \max(Wage, Assets \times 0.01)$
- If $DSR > 0.3$: $\Delta MPC_{debt} = -0.1$ (additional drop)

## 2. Implementation Guide

### Target: `simulation/decisions/ai_driven_household_engine.py`

#### [ADD] `adjust_consumption_for_interest_rate(self, household, base_agg, current_rate)`
- Inputs:
    - `household`: The agent instance.
    - `base_agg`: The original `agg_buy` from the AI Action Vector.
    - `current_rate`: The `nominal_rate` from market data.
- Logic: Compute $\Delta MPC_{savings}$ and $\Delta MPC_{debt}$.
- Return: `max(0.1, min(0.9, base_agg + delta_mpc))`

#### [REFACTOR] `make_decisions`
- Locate the loop over `goods_list`.
- Inside the loop, for each `item_id`:
    1. Get `base_agg = action_vector.consumption_aggressiveness.get(item_id, 0.5)`.
    2. Call `agg_buy = self.adjust_consumption_for_interest_rate(household, base_agg, nominal_rate)`.
    3. Use the adjusted `agg_buy` for subsequent willingness-to-pay and quantity calculations.

## 3. Verification

### Automated
1. Run `python scripts/iron_test.py`.
2. Check `MONETARY_TRANSMISSION` debug labels.
3. Observe `total_consumption` vs `interest_rate` correlation in history.

### Behavioral
- ANT agents should show much larger consumption volatility in response to rate changes.
- High-debt agents should maintain lower consumption even if they are "hungry" (if DSR is high).
