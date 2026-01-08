# Specification: Utility Maximization Logic (The Driver)

**Version**: 1.0
**Phase**: 14/15 Integration
**Objective**: Upgrade Agent Decision Engines from "Random/Rule-based" to "Utility-based" to support Durables and Credit.

---

## 1. Context & Motivation
*   **Current State**: Agents buy Food if `needs['survival'] > Threshold`. They work if `money < Threshold`.
*   **Problem**: This logic fails for Durables (Why buy a fridge if not hungry?) and Credit (Why pay interest?).
*   **Target State**: Agents calculate Expected Utility (EU) to make decisions. "Maximize $U = U_{now} + \beta U_{future}$".

## 2. Household Logic Upgrade ("The Rational Consumer")

### A. Utility Function for Durables
Instead of linear consumption, we define **Saturation**.
$$ U_{goods} = \sum_{i \in Assets} (Quality_i \times \text{Condition}_i) $$
*   **Marginal Utility (MU)**: The utility gained from *one additional unit*.
    *   First Fridge ($Q=1.0$): MU = 100 (Essential).
    *   Second Fridge ($Q=1.0$): MU = 10 (Convenience).
    *   Third Fridge: MU = 0 (Useless Space).
*   **Decision Rule**:
    *   `If MU > Price * Marginal_Value_of_Money`: **BUY**.
    *   `Else`: **SAVE**.

### B. Time Preference (Credit)
*   **Discount Factor ($\beta$)**: How much the agent values the future (e.g., 0.95).
*   **Purchase Decision with Loan**:
    *   Benefit: $U_{now}$ (Instant gratification of the Durable).
    *   Cost: $\sum \text{Interest Payments}$.
    *   **Rule**: Buy on Credit if $U_{goods} > \text{Total Interest Cost} \times \text{Risk_Aversion}$.

## 3. Firm Logic Upgrade ("The Rational Investor")

### A. Leverage Logic (ROI vs Rate)
*   **Metric**: Return on Invested Capital (ROIC).
*   **Scenario**:
    *   Current Profitability: 15%.
    *   Loan Interest Rate: 5%.
    *   **Action**: **BORROW MAX**. (The "Leverage Effect").
*   **Constraint**: Solvency Risk.
    *   If Debt/Equity > Safe_Limit (e.g., 2.0), stop borrowing.

## 4. Implementation Plan (Codebase)

### A. `simulation/decisions/household_decision_engine_new.py`
Modify `decide_purchases()`:
```python
def un_utility_score(item, current_assets):
    if item.is_durable and count(current_assets, item.type) >= 1:
        return 0.1 # Saturation
    return item.quality * 10
```

### B. `simulation/decisions/firm_decision_engine_new.py`
Modify `decide_financing()` (New Method):
```python
def decide_financing(self, firm, interest_rate):
    projected_roi = firm.calculate_historical_roi()
    if projected_roi > interest_rate + risk_premium:
        amount = firm.calculate_expansion_cost()
        return "REQUEST_LOAN", amount
    return "DO_NOTHING", 0
```

## 5. Roadmap Integration
1.  **Step 1**: Implement `Household.durable_saturation` logic in WO-025.
2.  **Step 2**: Implement `Firm.leverage_logic` in WO-024 (Banking).
3.  **Step 3**: Calibrate parameters so they don't bankrupt everyone instantly.
