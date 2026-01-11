# Work Order: WO-046 Adaptive Housing Brain

## Context
Phase 22 requires Households to exhibit "System 2" thinking in the property market. Currently, agents blindly buy houses if they have 20% down payment. We need to introduce an NPV-based decision model that considers **Opportunity Cost**.

## Objective
Update `HousingManager.should_buy` to compare:
1.  **Buy Option**: Buying the house and paying a mortgage.
2.  **Rent Option**: Renting the house and **investing the down payment** elsewhere.

## Instructions (Jules)

### 1. File Modification
Target: `simulation/decisions/housing_manager.py`

#### Modify `should_buy` Method
- **Signature Update**: Ensure it accepts or accesses `risk_free_rate` (default 0.05).
- **Logic Change**:
  - `Rent NPV` Calculation:
    - **Inflow**: Investment Return from `Down Payment` amount over the horizon (10 years).
      - Formula: `Down Payment * ((1 + risk_free_rate)^t - 1)` discounted? No, consider net wealth at horizon or stream of income.
      - Better Approach (Net Present Value of Flows):
        - Inflow: `Down Payment * risk_free_rate` per year (Interest Income).
        - Outflow: `Rent Price` per year.
        - `Rent NPV` = Sum of `(Inflow - Outflow) / (1 + discount_rate)^t`
  - `Buy NPV` Calculation:
    - **Inflow**: `Utility (Imputed Rent)` per year + `Future Property Value` (at horizon).
    - **Outflow**: `Mortgage Payment` + `Maintenance` + `Down Payment` (Initial).
    - `Buy NPV` = `Sum of Flows / Discount` + `Disc. Future Value` - `Down Payment`
  - **Decision**: Return `True` if `Buy NPV > Rent NPV`.

### 2. Constraints
- **Horizon**: 120 ticks (10 years).
- **Discount Rate**: 0.005 (0.5% per tick).
- **Risk Free Rate**: Use provided logic or default 0.05 (annual) -> convert to monthly.
- **Biases**: Maintain existing Optimism/Ambition biases impacting `perceived_appreciation` or `utility`.

### 3. Verification
Create a new test file: `tests/test_housing_decision.py`.
- **Test Case A (High Interest)**: Interest Rate 15%. Logic should prefer **RENTER** (high opportunity cost of down payment).
- **Test Case B (Low Interest)**: Interest Rate 1%. Logic should prefer **BUYER** (cheap leverage).

## Definition of Done
- `HousingManager.should_buy` implements the new comparison logic.
- Unit tests pass and demonstrate sensitivity to interest rates.
