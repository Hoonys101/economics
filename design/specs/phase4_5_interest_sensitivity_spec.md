# W-1 Spec: Phase 4.5 Organic Interest Sensitivity (Utility Competition)

> **Status**: REVISED (Organic Model)
> **Goal**: Replace hard-coded scaling with an ROI-based competition between Saving and Consumption.

## 1. Concept: Savings as a Product
A household compares the "Value" of spending $1 now versus saving it for the future.

### 1.1 Savings ROI Calculation
- **Real Rate ($r$)**: $r = \text{nominal\_rate} - \text{avg\_expected\_inflation}$
- **Time Preference ($\beta$)**:
    - **ANT** (`MISER`, `CONSERVATIVE`): 1.2
    - **NEUTRAL** (`GROWTH_ORIENTED`): 1.0
    - **GRASSHOPPER** (`STATUS_SEEKER`, `IMPULSIVE`): 0.8
- **Saving ROI ($U_s$)**: $U_s = (1 + r) \times \beta$

### 1.2 Consumption ROI Calculation (Per Item)
- **Need Value ($V_n$)**: Current value of the most relevant need satisfied by the item (e.g., survival need for food).
- **Market Price ($P$)**: Current `avg_traded_price`.
- **Consumption ROI ($U_c$)**: $U_c = V_n / P$

## 2. Decision Logic

### 2.1 The Competition
Inside the `make_decisions` loop for each `item_id`:
1.  Calculate $U_s$ and $U_c$.
2.  Apply **Substitution Effect**: 
    - If $U_s > U_c$:
        - Attenuate buying aggressiveness: `agg_buy = agg_buy * (U_c / U_s)`
        - This naturally slows down consumption when rates are high OR prices are high OR needs are low.

### 2.2 Cashflow Channel (The Hard Constraint)
While the substitution effect is organic, the **Debt Service Ratio (DSR)** represents a hard budget constraint.
- $DSR = \frac{\text{Daily Interest Burden}}{\max(\text{Wage}, \text{Assets} \times 0.01)}$
- If $DSR > \text{config.DSR\_CRITICAL\_THRESHOLD}$ (0.4):
    - `agg_buy = agg_buy * 0.5` (Emergency liquidity preservation).

## 3. Implementation Details

- **File**: `simulation/decisions/ai_driven_household_engine.py`
- **Method**: `_apply_monetary_transmission(self, household, market_data, item_id, base_agg)`
- **Integration**: Call this inside the `goods_list` loop to get the final `agg_buy`.

## 4. Verification

- Ant agents should stop buying `clothing` or `luxury_food` almost immediately when $r$ rises, while still buying `basic_food`.
- Grasshoppers should only stop buying when $r$ is extremely high or they hit the DSR wall.
