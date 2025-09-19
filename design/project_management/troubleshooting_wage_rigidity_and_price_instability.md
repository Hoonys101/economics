# Troubleshooting Guide: Wage Rigidity and Price Instability

## 1. Problem Recognition

The simulation currently suffers from a critical economic instability issue characterized by two primary symptoms:

1.  **Wage Rigidity:** The `avg_wage` metric remains static at or near the `BASE_WAGE` (10.0) for long periods, failing to respond to market conditions.
2.  **Price Instability:** The `food_avg_price` experiences explosive, uncontrolled growth (hyperinflation), quickly rising to levels that are unsustainable for the economy.

This combination leads to a "death spiral" where households can no longer afford essential goods, causing the economy to collapse.

## 2. Verification Method

This issue can be consistently reproduced by running the main simulation (`python main.py`) and examining the output in `results_baseline.csv`.

**Key Indicators:**

*   **`avg_wage` column:** Observe that the value is `0.0` when no hiring occurs, and jumps to `10.0` but does not increase further in a dynamic way.
*   **`food_avg_price` column:** Observe that the value increases exponentially from ~100 to over 300 within a short period.

## 3. Root Cause Analysis

The root cause is a systemic flaw in the price formation mechanism for the labor market, coupled with a positive feedback loop between food prices and household wage demands.

1.  **Symmetrical Price Setting:** Initially, both firms (buyers) and households (sellers) calculated their target wages using nearly identical formulas based on `BASE_WAGE`. This meant there was no real negotiation or price discovery; a transaction only occurred if both parties arrived at the same static number.

2.  **Insufficient Feedback Loop:** Subsequent attempts to introduce dynamic premiums (based on firm assets or hiring failures) were too small to overcome the core problem. The household's wage demand, tied to the exploding food prices, rose much faster than the firm's wage offers could keep up.

3.  **Positive Feedback Loop:** The core cycle of instability is as follows:
    *   Food prices increase slightly.
    *   Households, needing to afford food, increase their `reservation_wage`.
    *   Firms' wage offers do not increase proportionally, so no hiring occurs.
    *   Lack of labor leads to lower production of all goods, including food.
    *   Reduced food supply causes a further increase in food prices.
    *   The cycle repeats, leading to runaway inflation and market failure.

## 4. Documented Failed Attempts

To prevent repeating ineffective solutions, the following approaches have been tried and have failed to solve the root cause:

1.  **Asset-Based Premium:** An `asset_premium` was added to the firm's wage offer. This was insufficient as the premium was too small to bridge the gap between offer and ask prices.
2.  **Static Competitive Premium:** A small, fixed `competitive_premium` (0.5) was added if a firm failed to hire. This was also too small to have a meaningful effect against the rapidly rising reservation wages.
3.  **Market-Based Competitive Premium:** The logic was improved to have the wage offer based on the previous tick's `avg_wage`. While economically more sound, this also failed because the initial lack of transactions meant the `avg_wage` never moved from its base, so the feedback loop never started.

## 5. Recommended Next Steps

**Stop incremental patching of the wage formula.**

The problem is not in the specific coefficients of the wage calculation, but in the fundamental market design. Further attempts to tweak premiums or factors will likely fail.

The next action should be a **re-evaluation and redesign of the core market price-setting mechanism**. Potential avenues to explore:

*   **More Sophisticated Bidding:** Instead of placing orders at a single price, agents could submit a range of acceptable prices.
*   **Market-Clearing Price:** The `OrderBookMarket` could be enhanced to calculate a market-clearing price (e.g., where supply and demand curves intersect) rather than just matching identical bids and asks.
*   **Firm Profitability:** A firm's ability to offer higher wages should be more directly and strongly tied to its profitability from the previous ticks. A highly profitable firm should be willing to pay significantly more to maintain production.
