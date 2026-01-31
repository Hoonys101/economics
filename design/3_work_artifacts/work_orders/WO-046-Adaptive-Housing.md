# Work Order: Adaptive Housing Brain [Engineering Spec]

> [!IMPORTANT]
> **Spec-First Directive**: All formulas and logic are defined here. Implement EXACTLY as specified.
> **Architecture Update**: Use a dedicated System 2 module (`HouseholdSystem2Planner`) instead of cluttering existing managers.

## 1. System Architecture
* **New Module:** `simulation/ai/household_system2.py`
 * **Class:** `HouseholdSystem2Planner`
 * **Role:** Handles computationally expensive logic (System 2) for households.
* **Integration:**
 * `Household` agent calls `decide_housing()` -> Delegates to `HouseholdSystem2Planner.calculate_housing_npv()`.

## 2. Logic Specification (Algorithm)

### A. Input Data
The Planner must act on a snapshot of data:
* `current_wealth`: Household Assets (Cash + Deposits + Equities).
* `income`: Annual Income (`daily_wage * 360` approximation).
* `market_rent`: Current Monthly Rent (`daily_rent * 30`).
* `market_price`: Current Mean Housing Price.
* `interest_rate`: `risk_free_rate` (Annual).
* `price_growth_expectation`: Rolling average of price change (Last 1 year), **Capped at 5% (0.05)**.

### B. Decision Formulas (NPV Comparison)

**1. Buy Valuation (`NPV_Buy`)**
$$ NPV_{Buy} = \sum_{t=1}^{T} \frac{U_{shelter} - Cost_{own}}{(1+r)^t} + \frac{P_{future}}{(1+r)^T} - P_{initial} $$

* $T$: 10 years (Using **Monthly** steps, i.e., 120 months).
* $r$: Monthly Discount Rate (`(interest_rate + 0.02) / 12`).
* $P_{initial}$: `market_price`.
* $U_{shelter}$: `market_rent` (Utility gained by avoiding rent).
* $Cost_{own}$: `(market_price * 0.01) / 12` (Maintenance/Tax per month).
* $P_{future}$: `market_price * (1 + g)^10`. ($g$ = Capped expectation).

**2. Rent Valuation (`NPV_Rent`)**
$$ NPV_{Rent} = \sum_{t=1}^{T} \frac{Income_{invest} - Cost_{rent}}{(1+r)^t} + \frac{Principal}{(1+r)^T} $$

* $Principal$: Down Payment Amount (Assumed 20% of `market_price`).
 * *Note: This represents the Opportunity Cost of Equity.*
* $Income_{invest}$: `Principal * (interest_rate / 12)`.
* $Cost_{rent}$: `market_rent`.

### C. Final Decision Logic
```python
def decide(self, inputs):
 # 1. Safety Guardrail (DTI)
 loan_amount = inputs.market_price * 0.8
 annual_mortgage_cost = loan_amount * inputs.interest_rate
 if annual_mortgage_cost > inputs.income * 0.4:
 return "RENT" (Force Rent due to DTI)

 # 2. Rational Choice
 if npv_buy > npv_rent:
 return "BUY"
 else:
 return "RENT"
```

## 3. Implementation Steps
1. **Create Module**: `simulation/ai/household_system2.py`.
2. **Config**: Add `HOUSING_EXPECTATION_CAP = 0.05` to `config.py`.
3. **Integrate**: Modify `simulation/agents/household.py` to use `HouseholdSystem2Planner`.
4. **Verify**: Add tests in `tests/test_household_system2.py`.
