# W-1 Specification: Phase 4.5 - The Responsible Government (Revised)

> **Citation**: Revised based on Architect Prime's strategy and Second Architect's critical review.

## 1. Overview & Objectives
**Goal**: Transform the Government from a "Money Vacuum" into an "Intelligent Stabilizer".
**Core Problem**: Government hoards cash (taxes) -> Market liquidity dries up -> Households go bankrupt -> Extinction.
**Solution**: 
1.  **Fiscal Rule**: Automatically recycle excess cash back to households (Citizen Dividend).
2.  **Political Feedback**: Adjust tax rates based on "Approval Rating" to simulate political pressure.

---

## 2. Parameter Tuning (Survival First)
Before implementing logic, we must ensure agents don't die immediately.

### 2.1 Config Updates
*   **`INITIAL_HOUSEHOLD_ASSETS_MEAN`**: Increase from `5000.0` to `20000.0` (Give them a runway).
*   **`HOUSEHOLD_DEATH_TURNS_THRESHOLD`**: Increase from `4` to `10` (More leniency for starvation).
*   **`UNEMPLOYMENT_BENEFIT_RATIO`**: Maintain at `0.7` or higher.

---

## 3. The Political System (Approval Logic)

### 3.1 The Approval Function
Each household evaluates the government every tick.

$$Score_i = (S_{survival} \times w_{1}) + (S_{relative} \times w_{2}) + (S_{future} \times w_{3}) - (S_{tax} \times w_{4} \times P_{sen})$$

#### Components:
1.  **$S_{survival}$ (Survival)**:
    *   If Employed: $\min(\frac{Wage}{SurvivalCost} - 1, 1.0)$
    *   If Unemployed: $\min(\frac{Benefit}{SurvivalCost} - 1, 0.0)$ (Usually negative)
2.  **$S_{relative}$ (Inequality)**:
    *   $\ln(\frac{MyAssets}{AvgAssets} + e)$ (Positive if above average, Negative if below)
3.  **$S_{future}$ (Growth)**:
    *   $\text{GDP\_Growth\_Rate} \times 10$
4.  **$S_{tax}$ (Pain)**:
    *   $\text{Effective\_Tax\_Rate}$ (0.0 ~ 1.0)

#### Weights (Configurable):
*   $w_1 = 1.0$ (Survival is paramount)
*   $w_2 = 0.5$ (Inequality matters, but less than food)
*   $w_3 = 0.5$ (Hope matters)
*   $w_4 = 2.0$ (Taxes deny immediate gratification)

#### Personality Sensitivity ($P_{sen}$):
*   `MISER`: 1.5 (Hates taxes)
*   `SOCIAL`: 0.8 (Tolerates taxes for welfare)
*   Others: 1.0

### 3.2 Output
*   **Binary Support**: If $Score_i > 0$, `support = True` (1), else `False` (0).
*   **Metric**: `Government.approval_rating` = $\frac{\sum support}{TotalPop}$.

---

## 4. The Fiscal Rules (Logic Loop)

### 4.1 The "Use-it-or-Lose-it" Rule (Liquidity Recycling)
Periodically (every tick or every 10 ticks), the government checks its coffers.

1.  **Calculate Target Reserve**:
    *   `Target = Last_GDP * 0.10` (Buffer for 10% of GDP)
2.  **Check Surplus**:
    *   `Excess = Cash - Target`
3.  **Inflation Check**:
    *   If `CPI_Growth > 0.05` (5%): **HALT DISTRIBUTION** (Cool down economy).
4.  **Distribute**:
    *   If `Excess > 0` AND No Inflation Warning:
        *   `Payout = Excess * 0.3` (Dampened - don't dump all variables at once).
        *   `distribute_dividend(Payout / Pop)` to all households.

### 4.2 Tax Rate Adjustment (Political Response)
Government adjusts `INCOME_TAX_RATE` to maximize Approval (or survive).

1.  **If Approval < 40% (Crisis Mode)**:
    *   **Lower Tax**: `Rate -= 0.01` (1% point cut).
    *   **Or Increase Benefit**: If Tax is already low, boost Welfare.
2.  **If Approval > 60% (Political Capital)**:
    *   **Raise Tax**: `Rate += 0.01` (to build reserves/infrastructure).
3.  **Bounds**:
    *   `MIN_TAX = 0.05`
    *   `MAX_TAX = 0.50`

---

## 5. Verification Plan
1.  **Scenario**: Run 1000 ticks.
2.  **Expectation**:
    *   Government Cash should stabilize (not grow to infinity).
    *   Active Households should remain > 15 (out of 20).
    *   Approval Rating should oscillate between 40~60%.
