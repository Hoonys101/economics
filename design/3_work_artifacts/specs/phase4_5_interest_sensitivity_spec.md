# W-1 Spec: Phase 4.5 Organic Interest Sensitivity (Utility Competition)

> **Status**: REVISED (Organic Model)
> **Goal**: Replace hard-coded scaling with an ROI-based competition between Saving and Consumption.

## 1. Concept: The 3 Pillars of Desire
Instead of simple binary logic, agents' internal conflict is driven by three competing desires.

### 1.1 The Pillars
- **Wealth (preference_asset)**: Desire for future safety and capital growth. Driven by interest rates.
- **Social (preference_social)**: Desire for status and relative positioning. Driven by brand value and luxury.
- **Growth (preference_growth)**: Desire for survival and self-improvement. Driven by basic needs.

### 1.2 Utility Formulas
1. **Saving ROI ($U_{save}$)**:
   $$U_{save} = (1 + r_{real}) \times preference\_asset$$
2. **Consumption ROI ($U_{consume}$)**:
   - For Basic Goods: $U_{c} = (NeedValue / Price) \times preference\_growth$
   - For Luxury/Brand: $U_{c} = (BrandValue / Price) \times preference\_social$

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
