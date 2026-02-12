# Insight Report: Fix Final Penny-Standard Regressions (PH15-FIX)

## 1. Overview
This mission focused on resolving the last 3 test failures caused by the "Penny Standard" migration (switching from float dollars to integer pennies). The failures were due to mismatched scale assumptions (100x), improper mocking of financial agents, and missing attributes in test stubs.

## 2. Key Resolutions

### A. 100x Scale Mismatch in Fiscal Policy
- **Issue**: `FiscalPolicyManager` expects market prices in Dollars (float) and multiplies them by 100 to convert to Pennies. The unit test `test_fiscal_policy_manager.py` provided `1000.0` (thinking it was pennies or intending $1000), which resulted in a survival cost of 100,000 pennies ($1000). The test assertion expected brackets based on 1000 pennies ($10).
- **Fix**: Updated the test input to `10.0` (Dollars), which correctly converts to 1000 pennies, aligning with the assertion.

### B. Mock Fragility in Government Integration (TypeError)
- **Issue**: `TaxService.collect_wealth_tax` calls `agent.get_balance(currency)` which returns an `int`. The test mocks in `tests/modules/government/test_government_integration.py` did not configure `get_balance` to return a value, causing it to return a `MagicMock` object. This triggered a `TypeError` when compared with an integer threshold.
- **Fix**: Explicitly configured `agent.get_balance.return_value` to return integer penny amounts in the mocks.

### C. Config Ambiguity & Welfare Floor (Assertion Error)
- **Issue**:
    1. `test_government_integration.py` (Integration) asserted a tax of 380 pennies but got 400. This was because `WEALTH_TAX_THRESHOLD` was set to `1000.0` (1000 pennies), whereas the test logic assumed 100,000 pennies ($1000).
    2. The welfare benefit assertion expected 10 pennies, but got 500. This was due to a hidden logic floor in `WelfareManager`: `max(survival_cost, 1000)`. The test input implied a survival cost of 20 pennies, which was overridden by the 1000-penny floor ($10 minimum).
- **Fix**:
    1. Updated `WEALTH_TAX_THRESHOLD` to `100000` (pennies).
    2. Updated the welfare benefit assertion to `500` (50% of the 1000-penny floor) and documented the floor logic in the test.

### D. Missing QE Support in Test Stub
- **Issue**: `FinanceSystem.issue_treasury_bonds` contains logic to check `government.sensory_data.current_gdp` for QE triggers. The `StubGovernment` used in `test_system.py` lacked `sensory_data`.
- **Fix**: Added `sensory_data` mock and `current_gdp` attribute to `StubGovernment`.

## 3. Technical Debt Observations

| ID | Module | Description | Status |
| :--- | :--- | :--- | :--- |
| **TD-TEST-SCALE** | Tests | Unit tests mix Dollar and Penny inputs without explicit type/variable naming (e.g., `price` vs `price_pennies`). | Mitigated (Local Fix) |
| **TD-WELFARE-FLOOR** | Government | `WelfareManager` has a hardcoded floor of 1000 pennies ($10) for survival cost, which might not scale with config changes. | Identified |
| **TD-MOCK-TYPE** | Tests | Mocks often lack type enforcement (`spec=IAgent`), allowing missing methods (`get_balance`) to fail late at runtime. | Ongoing |

## 4. Recommendations
- **Strict Typing for Money**: Adopt `Money` value objects or strictly name variables `amount_pennies` vs `amount_dollars` to prevent 100x errors.
- **Review Hardcoded Floors**: The 1000-penny floor in `WelfareManager` should be configurable (`MIN_SURVIVAL_COST`).
