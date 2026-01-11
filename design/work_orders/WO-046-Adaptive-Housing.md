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

### 1. File Modification
Target: `simulation/decisions/housing_manager.py`

#### Modify `should_buy` Method
- **Signature Update**: Ensure it accepts or accesses `risk_free_rate` (default 0.05).
- **Revised Logic (Cash Flow & Terminal Value Approach)**:
  Compare the **Net Present Value (NPV)** of total wealth change over the horizon.

  - **A. Rent Scenario**:
    - **Initial**: Keep `Down Payment` as Cash (Invested).
    - **Flows (t=1..120)**:
      - Inflow: `Down Payment * (risk_free_rate / 12)` (Monthly Investment Income).
      - Outflow: `Rent Price`.
    - **Terminal (t=120)**:
      - Inflow: `Down Payment` (Principal Recovery).
    - **NPV_Rent** = `Sum( (InvIncome - Rent) / (1+r)^t )` + `(DownPayment / (1+r)^120)`

  - **B. Buy Scenario**:
    - **Initial**: Pay `Down Payment` (Outflow).
    - **Flows (t=1..120)**:
      - Outflow: `Mortgage Payment` + `Maintenance`.
      - (Note: Do NOT add "Imputed Rent/Utility" as a monetary inflow here. The benefit of owning is simply *not paying rent*.)
      - Inflow: `Prestige Bonus` (subjective utility, add as stream or lump sum. Recommendation: Add 1/120 of bonus per tick to represent ongoing satisfaction).
    - **Terminal (t=120)**:
      - Inflow: `Future Property Value` (Price * (1 + appreciation)^120).
    - **NPV_Buy** = `-DownPayment` + `Sum( (Prestige - Mortgage - Maint) / (1+r)^t )` + `(FutureValue / (1+r)^120)`

  - **Decision**: Return `True` if `NPV_Buy > NPV_Rent`.

### 2. Constraints & Clarifications
- **Horizon**: 120 ticks (10 years).
- **Discount Rate**: 0.005 (0.5% per tick).
- **Interest Rate Conversion**: Use **Simple Division** (Annual / 12) for monthly approximation.
- **Prestige Bonus**: treat as a subjective **Inflow** in the Buy Scenario.
- **Principal Recovery**: MUST be included in the Rent Scenario (Terminal Value).

### 3. Verification
Create a new test file: `tests/test_housing_decision.py`.
- **Test Case A (High Interest)**: Interest Rate 15%. Logic should prefer **RENTER** (high opportunity cost of down payment).
- **Test Case B (Low Interest)**: Interest Rate 1%. Logic should prefer **BUYER** (cheap leverage).

## Definition of Done
- `HousingManager.should_buy` implements the new comparison logic.
- Unit tests pass and demonstrate sensitivity to interest rates.
