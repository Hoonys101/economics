# Technical Report: Integration & Stress Test Regressions

## Executive Summary
The integration and stress test suites are experiencing critical failures due to a contract mismatch in the `MarketSnapshotDTO` definition and method name discrepancies in the `ISettlementSystem` interface. The primary issue is a `TypeError` caused by a missing `market_data` argument in `MarketSnapshotDTO` instantiations, following an API update that made this field mandatory.

## Detailed Analysis

### 1. MarketSnapshotDTO Signature Mismatch
- **Status**: ❌ Missing (Causes `TypeError`)
- **Evidence**: 
    - `modules\system\api.py:L57`: `MarketSnapshotDTO` defines `market_data: Dict[str, Any]` as its third positional argument without a default value.
    - `tests\integration\test_decision_engine_integration.py:L142, L174, L200, L226`: Calls `MarketSnapshotDTO(tick=1, market_signals={}, housing=None, loan=None, labor=None)`, omitting `market_data`.
    - `tests\integration\scenarios\test_stress_scenarios.py:L268-273`: Instantiates the DTO with `tick`, `housing`, `labor`, and `market_signals`, but skips `market_data`.
- **Notes**: This is a direct violation of the "DTO Purity" mandate. The DTO was expanded to support generic market data, but the test constructors were not updated to match the new schema.

### 2. Settlement System "Expected Call Not Found"
- **Status**: ⚠️ Partial / Incorrect Mocking
- **Evidence**:
    - `tests\integration\scenarios\test_stress_scenarios.py:L106`: Asserts that `event_system.settlement_system.create_and_transfer` was called.
    - `tests\integration\mission_int_02_stress_test.py:L74`: Shows a `MockSettlementSystem` implementing `mint_and_distribute` for the same logical operation (injecting assets).
- **Diagnosis**: The `EventSystem` logic likely calls `mint_and_distribute` to align with the Central Bank's money-creation logic (as per `MockSettlementSystem`), rendering the test's expectation of `create_and_transfer` obsolete.

### 3. Personality Enum Regression
- **Status**: ✅ Partially Patched
- **Evidence**: `tests\integration\scenarios\test_stress_scenarios.py:L43`
- **Notes**: The test code explicitly notes that `Personality.NORMAL` is now invalid and has been replaced with `Personality.CONSERVATIVE`. This confirms an uncoordinated change in the `Personality` enum that required manual test intervention.

## Special Format: Test Doctor

1. **Failing Module**: `tests\integration\test_decision_engine_integration.py::test_firm_places_sell_order_for_food`
2. **Error**: `TypeError: MarketSnapshotDTO.__init__() missing 1 required positional argument: 'market_data'`
3. **Diagnosis**: `MarketSnapshotDTO` in `modules/system/api.py` was updated to include a mandatory `market_data` field. Test instantiations must be updated to include `market_data={}` or appropriate data.

1. **Failing Module**: `tests\integration\scenarios\test_stress_scenarios.py::test_hyperinflation_trigger`
2. **Error**: `AssertionError: Expected call to 'create_and_transfer' but it was never called.`
3. **Diagnosis**: The system has transitioned from `create_and_transfer` to `mint_and_distribute` (or similar) to better reflect Central Bank operations. The test mock and assertion names are out of sync with the implementation.

## Risk Assessment
- **Zero-Sum Integrity**: The shift from `create_and_transfer` to `mint_and_distribute` without proper auditing in tests risks masking "magic money" creation bugs if the injection logic is not strictly bounded.
- **API Staleness**: The failure to update tests alongside `api.py` changes suggests that automated type checking (`mypy`) is either not being run on the test suite or its warnings are being ignored.

## Conclusion
The regressions are mechanical results of evolving API contracts. To restore the "Golden Cycle," all `MarketSnapshotDTO` calls must be updated to include `market_data`, and the `EventSystem` tests must be aligned with the current `ISettlementSystem` method signatures (specifically checking for `mint_and_distribute` or `create_and_transfer` based on the final Protocol definition).