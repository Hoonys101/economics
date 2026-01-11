# Work Order: WO-046 Adaptive Housing Brain [Engineering Spec]

> [!IMPORTANT]
> **Spec-First Directive**: All formulas and logic are defined here. Implement EXACTLY as specified. Do not invent new logic.

## 1. Core Logic: When to Decide? (Trigger Conditions)
We optimize performance by restricting *when* the System 2 logic runs.

**Implement in `Household.decide_housing()`:**
- **homeless**: Calculate every tick (Priority).
- **tenant**: Calculate only if `contract_remaining < 30` (Expiration imminent).
- **wealth_shock**: Calculate if `cash > memory['last_check_cash'] * 1.2` (Rich enough to reconsider).

## 2. Decision Logic (NPV Formula)

**Class: `HousingManager`**
**Method: `should_buy(property_price, rent_price, market_data)`**

### A. Buy Valuation (`NPV_Buy`)
$$ NPV_{Buy} = \sum_{t=1}^{T} \frac{U_{shelter} - Cost_{own}}{(1+r)^t} + \frac{P_{future}}{(1+r)^T} - P_{initial} $$

- **$P_{initial}$**: `property_price` (Asking Price).
- **$U_{shelter}$**: `rent_price` (Avoiding rent is the utility).
- **$Cost_{own}$**: `MortgagePayment` + `Maintenance` (0.1% of price/tick).
- **$P_{future}$**: `property_price * (1 + min(trend, 0.05/12))^T`.
  - **Constraint**: `trend` is capped at 5% annual (`MAX_EXPECTATION`) to prevent FOMO.
- **$r$**: `risk_free_rate` / 12 (Monthly Discount Rate).
- **$T$**: 120 ticks (10 years).

### B. Rent Valuation (`NPV_Rent`)
$$ NPV_{Rent} = \sum_{t=1}^{T} \frac{Income_{invest} - Cost_{rent}}{(1+r)^t} + \frac{Principal}{(1+r)^T} $$

- **$Principal$**: `Down Payment` amount (Assumed 20% of `property_price` that *would* have been spent).
- **$Income_{invest}$**: `Principal * r` (Monthly Risk-free return).
- **$Cost_{rent}$**: `rent_price`.

### C. Final Decision
```python
if dti_ratio > 0.4: return False  # Safety Guardrail (Debt-to-Income)
return NPV_Buy > NPV_Rent
```

## 3. Implementation Details

### Required Helper Methods
- `_calculate_mortgage_payment(principal, rate, years=30)`: Standard amortization formula.
- `_get_price_trend(market_data)`: Extract rolling average price change.

### Logic Placement
- **Location**: `simulation/decisions/housing_manager.py`
- Modify `should_buy` to implement the formulae above STRICTLY.

## 4. Verification (Unit Test)
- **File**: `tests/test_housing_spec.py`
- **Case 1 (Bubble)**: High Trend (>10%) -> Capped at 5% -> Check Decision.
- **Case 2 (High Rate)**: Interest Rate 15% -> Rent Limit (High Opportunity Cost).
- **Case 3 (DTI Fail)**: `NPV_Buy` is high, but Income is low -> Return False.
