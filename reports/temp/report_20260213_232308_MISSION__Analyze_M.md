# Technical Report: Market DTO Schema Desync Analysis

## Executive Summary
An audit of the `modules\system\api.py` and current test failure logs reveals a significant schema mismatch between the defined Market DTOs and their instantiation in various modules and tests. The primary issues stem from outdated constructor calls that omit newly required fields (e.g., `market_data`, `total_bid_quantity`) or include obsolete ones (`exchange_rates`).

## Detailed Analysis

### 1. MarketContextDTO Schema Mismatch
- **Status**: ⚠️ Partial / ❌ Desynced
- **Evidence**: `modules\system\api.py:L21-27`
- **Findings**: The DTO is defined with three fields: `market_data`, `market_signals`, and `tick`.
- **Issue**: Test `test_adjust_marketing_budget` (and others in `test_sales_engine_refactor.py`) attempts to pass `exchange_rates` as a keyword argument. This field is not present in the current `api.py` definition.
- **Root Cause**: Regression or incomplete refactoring during currency/market context updates.

### 2. MarketSnapshotDTO Positional Argument Deficiency
- **Status**: ❌ Desynced
- **Evidence**: `modules\system\api.py:L84-96`
- **Findings**: `MarketSnapshotDTO` requires `tick`, `market_signals`, and `market_data` as mandatory positional arguments.
- **Issue**: Multiple tests (e.g., `test_agent_decision.py:L29`, `test_stress_scenarios.py:L327`, `test_decision_unit.py:L95`) are failing with `TypeError: missing 1 required positional argument: 'market_data'`.
- **Notes**: Callers appear to be using an older signature that only required `tick` and `market_signals`.

### 3. MarketSignalDTO Extended Schema Violation
- **Status**: ❌ Desynced
- **Evidence**: `modules\system\api.py:L28-44`
- **Findings**: The `MarketSignalDTO` was expanded to include `total_bid_quantity`, `total_ask_quantity`, and `is_frozen`.
- **Issue**: 
    - `test_public_manager_integration.py:L66` and `test_public_manager.py:L33` are missing 2 arguments (`total_bid_quantity`, `total_ask_quantity`).
    - `test_household_ai.py:L78` is missing 3 arguments (including `is_frozen`).
- **Notes**: These fields are mandatory (non-optional) in the `dataclass(frozen=True)` definition.

## Test Doctor Summary

1. **Failing Module**: `tests/unit/test_sales_engine_refactor.py::test_adjust_marketing_budget`
2. **Error**: `TypeError: MarketContextDTO.__init__() got an unexpected keyword argument 'exchange_rates'`
3. **Diagnosis**: Remove `exchange_rates` from the caller or update `MarketContextDTO` in `modules/system/api.py` if currency rates are required for decision making.

1. **Failing Module**: `tests/integration/scenarios/diagnosis/test_agent_decision.py::test_case`
2. **Error**: `TypeError: MarketSnapshotDTO.__init__() missing 1 required positional argument: 'market_data'`
3. **Diagnosis**: Update the constructor call at `test_agent_decision.py:29` to include a `market_data` dictionary.

1. **Failing Module**: `tests/unit/test_household_ai.py`
2. **Error**: `TypeError: MarketSignalDTO.__init__() missing 3 required positional arguments: 'total_bid_quantity', 'total_ask_quantity', and 'is_frozen'`
3. **Diagnosis**: Update `MarketSignalDTO` instantiation to provide volume and status data (likely `0.0, 0.0, False` for mocks).

## Risk Assessment
- **Integration Instability**: The core `SimulationState` (defined in `simulation\dtos\api.py`) relies on these DTOs. If the schema is not unified, downstream AI decision modules will receive malformed data or crash during initialization.
- **Mock Fragility**: Most failures are in test setups, indicating that mock factory functions for these DTOs were not updated alongside the API changes.

## Conclusion
The `modules\system\api.py` has been updated with more granular market data fields (Phase 1/33 requirements), but the corresponding test suites and mock generators are lagging behind. Immediate remediation is required in the test utilities to align with the new positional requirements of `MarketSnapshotDTO` and `MarketSignalDTO`.