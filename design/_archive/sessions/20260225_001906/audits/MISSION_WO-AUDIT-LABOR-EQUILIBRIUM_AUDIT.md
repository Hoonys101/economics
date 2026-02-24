# WO-AUDIT-LABOR-EQUILIBRIUM: Labor Market & Wage Stickiness Audit

## Executive Summary
The labor market is currently trapped in a "Deadlock Mismatch" where high household reservation wages—inflated by systemic money supply leaks (OMO bugs)—exceed the liquidity-constrained offers of firms. This is compounded by the total absence of `hidden_talent` heuristics, forcing the AI to rely on a shallow two-factor (Major/Education) matching logic that fails to clear the market.

---

## Detailed Analysis

### 1. Reservation Wage vs. Firm Liquidity
- **Status**: ⚠️ Partial (Mechanically enforced, but economically disconnected)
- **Evidence**: 
    - `modules/labor/system.py:L101-105`: A hard filter `if base_score < 1.0: continue` (where `base_score = offer / reservation`) prevents any match where the wage demand is even 1 penny above the offer.
    - `reports/diagnostic_refined.md`: Multiple `SETTLEMENT_FAIL` and `LIQUIDATION_TRIGGERED` events (e.g., Firm 123 insolvent due to "Unpaid Wage") indicate that while households demand high wages, firms have $0 cash or insufficient funds for existing obligations.
- **Notes**: There is no "Desperation Logic" in `modules/labor/system.py` to lower reservation wages after consecutive ticks of unemployment, leading to permanent stickiness.

### 2. Hidden Talent Analysis
- **Status**: ❌ Missing (Not Found)
- **Evidence**: 
    - `modules/labor/system.py:L112-136`: The `final_score` calculation exclusively uses `major_multiplier` and `edu_multiplier`. 
    - `simulation/dtos/api.py`: The `AgentStateData` and `JobSeekerDTO` (referenced in `modules/labor/system.py:L48`) do not contain a `hidden_talent` field.
- **Notes**: The absence of this field removes the "High-Performance" weighting from AI hiring. Firms cannot distinguish between a high-potential worker and a baseline worker if their Major/Education match, leading to low-quality hiring signals and eventual supply chain collapse.

### 3. Wage-Price Spiral (OMO Bug Impact)
- **Status**: ✅ Verified (Systemic Inflation)
- **Evidence**: 
    - `reports/diagnostic_refined.md:L13-L84`: Massive money supply divergence. 
        - **Tick 3**: Delta = 499,697.56
        - **Tick 60**: Delta = 11,085,067.46 (Actual: 24.1M vs Expected: 13.1M).
    - `simulation/ai/firm_ai.py:L74-75`: AI discretizes cash levels up to `10000+`. As the OMO bug pumps millions into the system, "Cash Levels" appear high in the state space, causing firms to raise prices (`q_sales`) and households to raise reservation wages to maintain purchasing power.
- **Notes**: The 85% money supply error is the primary driver of the unrealistic reservation wage floors.

---

## Architectural Insights
- **Heuristic Depth**: The `LaborMarket.match_market` logic is too deterministic. It requires a `probabilistic_fit` or `hidden_talent` variance to allow for "unconventional" matches during economic downturns.
- **Liquidity Awareness**: The `JobOfferDTO` is posted based on `price_pennies` (`modules/labor/system.py:L214`), but does not check if the firm actually has the escrowed cash to back the offer, leading to the `SETTLEMENT_FAIL` loop seen in diagnostics.

## Conclusion
The labor market "Mismatch" is a rational response by agents to a broken monetary environment. Households demand high wages because the OMO bug indicates an abundance of money, but firms face local liquidity crises and insolvency. Without `hidden_talent` to justify higher wages for specific workers, and without a fix for the OMO inflation, the market will remain frozen.

---

## Technical Report: `communications/insights/WO-AUDIT-LABOR-EQUILIBRIUM.md`

```markdown
# Insight Report: Labor Market Equilibrium Audit (WO-AUDIT-LABOR-EQUILIBRIUM)

## 1. Architectural Insights
*   **Hard Filter Bottleneck**: `modules/labor/system.py:L101` implements a binary reservation wage filter. In a volatile economy, this prevents "Wage Concession" cycles, causing permanent unemployment.
*   **Heuristic Poverty**: The matching engine lacks the `hidden_talent` attribute. Hiring is currently a "Commodity Purchase" based only on Education/Major, which ignores the productivity variance required for firm survival.
*   **Monetary Decoupling**: The OMO bug (Tick 60 Delta: 11M) creates a "False Wealth Effect" for households, jacking up reservation wages while firms are actually insolvent.

## 2. Regression Analysis
*   No existing tests were modified. However, `test_labor_market_logic` (if existing) would likely fail to detect this "Frozen Market" because it tests functionality, not economic equilibrium.
*   Refactoring `match_market` to include `hidden_talent` will require updating `JobSeekerDTO` and all factory methods in `tests/`.

## 3. Test Evidence
(Simulation Runtime Verification Required for Full Pass)
*   **Verified**: `modules/labor/system.py` passes static type checking.
*   **Verified**: `reports/diagnostic_refined.md` confirms the OMO inflation bug is active.

```