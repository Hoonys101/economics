# Technical Report: Household Module DTO Regression Analysis

## Executive Summary
The `MarketSnapshotDTO` in `modules/system/api.py` has been updated with a mandatory `market_data` field, causing instantiation failures in `tests/unit/modules/household/test_decision_unit.py`. Positional argument shifting due to this new field further misaligns `housing`, `loan`, and `labor` snapshots.

## Detailed Analysis

### 1. MarketSnapshotDTO Signature Mismatch
- **Status**: ❌ Missing / Regressed
- **Evidence**: 
    - `modules/system/api.py:L76-83`: `MarketSnapshotDTO` definition requires `market_data: Dict[str, Any]` as the third positional argument.
    - `tests/unit/modules/household/test_decision_unit.py:L101-107`: Instantiation omits `market_data`, passing `housing` into the `market_data` slot.
- **Notes**: Because `market_data` lacks a default value, passing keyword arguments for `housing`, `loan`, and `labor` without `market_data` results in a `TypeError`.

### 2. Positional Argument Shifting
- **Status**: ⚠️ Partial / Broken Logic
- **Evidence**: `test_decision_unit.py:L149-155`
- **Notes**: Even if `TypeError` is bypassed, the internal mapping of snapshots is likely corrupted because the test logic expects the 3rd argument to be `housing`, but it is now `market_data`.

### 3. MarketSignalDTO Complexity
- **Status**: ⚠️ Partial
- **Evidence**: `modules/system/api.py:L31-45`
- **Notes**: `MarketSignalDTO` now contains 13 required fields. While the current tests use an empty dict `{}` for `market_signals`, any future test data generation or logic requiring real signals will fail if all 13 fields are not provided.

## Risk Assessment
- **Type Safety**: The use of `Optional` fields after a new mandatory field in a Dataclass (without defaults) is a high-risk pattern for regressions.
- **Test Fragility**: Tests are manually constructing complex DTOs rather than using factories, making them highly susceptible to API signature changes.

## Conclusion
The Household module tests are currently broken due to the `system.api` DTO evolution. To restore integrity, `test_decision_unit.py` must be updated to include the `market_data={}` argument in all `MarketSnapshotDTO` calls.

---

### Special Format: Test Doctor
1. **Failing Module**: `tests/unit/modules/household/test_decision_unit.py::TestDecisionUnit::test_orchestrate_housing_buy`
2. **Error**: `TypeError: __init__() missing 1 required positional argument: 'market_data'`
3. **Diagnosis**: `MarketSnapshotDTO` was modified to include `market_data` as a required field; update test instantiations at L101 and L149 to include `market_data={}`.