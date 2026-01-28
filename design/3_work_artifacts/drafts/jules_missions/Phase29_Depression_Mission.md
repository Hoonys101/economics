# Mission: Invoke the Crisis (Phase 29 - The Great Depression)

## Context
Architect Prime has declared the "Component Era" officially open. We must now stress-test our newly refactored `FinanceDepartment` and `CorporateManager` under extreme economic pressure.

## Task Details

### 1. Scenario Configuration
- **File**: `config/scenarios/phase29_depression.json`
- **Actions**:
    - Set `base_interest_rate_multiplier`: `3.0` (200% Increase).
    - Set `corporate_tax_rate_delta`: `0.1` (10%p Increase).
    - Set `demand_shock_multiplier`: `0.7` (30% reduction in consumer spending).

### 2. Implementation of Stress Observations
- Update the simulation runner or a dedicated validation test to:
    - **Verify Interest Expense**: Ensure `FinanceDepartment` correctly calculates the surging interest costs on existing debt.
    - **Observe Altman Z-Score**: Monitor firms as they approach the "Danger" zone (Z < 1.1).
    - **Verify Corporate Resilience**: Confirm that `CorporateManager` detects the liquidity crisis and automatically triggers `pay_dividend_payout(0.0)` for distressed firms.

### 3. Verification & Reporting
- Run the simulation for 20 ticks using the Phase 29 scenario.
- Generate a summary report:
    - Number of firms entering the Z-Score danger zone.
    - Total dividend payout reduction across the sector.
    - Confirmation that no `CalculationError` or `StateInconsistency` occurred during the shock.

## Success Criteria
- ✅ Phase 29 scenario file created and functional.
- ✅ Successful observation of "Dividend Suspension" in crisis firms.
- ✅ FinanceDepartment survives the shock with accurate net profit accounting.
