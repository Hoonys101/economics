# Work Order: (The Portfolio Manager)

**Phase**: 16 (Portfolio Optimization)
**Assignee**: Jules (Manager AI)
**Status**: Draft

## 1. Goal
Implement a "Rational Investor" brain for Households that automatically rebalances assets between **Cash**, **Bank Deposits**, and **Firm Investments** (Startups) based on:
1. **Risk Aversion** (Personality)
2. **Expected Returns** (Yields)
3. **Portfolio Utility Maximization**

## 2. Theoretical Framework
We shift from "Accidental Savings" to "Conscious Allocation".
The agent maximizes:
$$ U = E(R) - \lambda \sigma^2 $$

* $E(R)$: Weighted Expected Return (Cash=0%, Deposit=Rate, Equity=Dividend%)
* $\lambda$ (Lambda): Risk Aversion Coefficient (0.1 ~ 10.0)
* $\sigma^2$: Portfolio Variance (Risk)

## 3. Implementation Plan

### Task 1: Personality Injection
* **Module**: `simulation/core_agents.py`
* **Class**: `Household`
* **Change**: Add `risk_aversion` float to `__init__`.
 * Value Range: `0.1` (Gambler) to `10.0` (Super Conservative).
 * Distribution: Random Gaussian or Uniform.

### Task 2: The Portfolio Manager Logic
* **Module**: `simulation/decisions/portfolio_manager.py` (New)
* **Class**: `PortfolioManager`
* **Method**: `optimize_portfolio(...)`
 * **Inputs**:
 * `total_liquid_assets` (Cash + Deposits)
 * `risk_aversion`
 * `risk_free_rate` (Bank Deposit Rate)
 * `inflation_expectation` (CPI change)
 * **Logic**:
 1. **Safety Margin**: Calculate 3 months of survival cost. This amount MUST be kept in Cash/Risk-Free Deposit.
 2. **Surplus Allocation**:
 * Compare $R_{deposit}$ vs $R_{equity}$.
 * If $R_{equity} > R_{deposit} + \text{RiskPremium}(\lambda)$, allocate to Equity.
 * Else, keep in Deposit.
 3. **Output**: Target allocations (Amount to Deposit, Amount to Invest).

### Task 3: Integration (Monthly Rebalancing)
* **Module**: `simulation/decisions/ai_driven_household_engine.py`
* **Method**: `make_decisions`
* **Trigger**: Run rebalancing logic only if `tick % 30 == 0`.
* **Action**:
 1. Call `portfolio_manager.optimize_portfolio()`.
 2. Generate `DEPOSIT` or `WITHDRAW` orders for the Loan Market.
 3. Generate `INVEST` orders (Startup) if surplus exists and risk appetite allows.

### Task 4: Verification (The Friedman Effect)
* **Script**: `scripts/verify_portfolio.py`
* **Scenario**:
 1. Run simulation.
 2. At T=50, Central Bank raises rates significantly.
 3. **Expectation**: Household Deposits should spike, Consumption/Startup should cool down.

## 4. Artifacts to Create
* `simulation/decisions/portfolio_manager.py`
* `scripts/verify_portfolio.py`

## 5. Definition of Done
* Households explicitly move money to Bank (Deposit) when they have excess cash.
* "Risk Averse" agents hold mostly Deposits.
* "Risk Loving" agents attempt Startups more often.
* Simulation verifies the correlation between Interest Rate and Deposit Volume.
