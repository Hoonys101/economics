# Technical Report: Market DTO Schema Desync Analysis

## Executive Summary
There is a critical schema mismatch between the centralized DTO definitions in `modules/system/api.py` and their respective call sites across the simulation engine and test suites. Recent architectural shifts toward strict `@dataclass` usage have introduced breaking changes, specifically regarding mandatory positional arguments and unsupported keyword arguments.

## Detailed Analysis

### 1. MarketContextDTO: Unexpected Keyword Argument
- **Status**: ❌ Schema Mismatch
- **Evidence**: `modules/system/api.py:L14-20` vs `regress_market_dtos.log`
- **Findings**: `MarketContextDTO` is defined as a dataclass with only three fields: `market_data`, `market_signals`, and `tick`. However, callers in `test_sales_engine_refactor.py` are attempting to pass `exchange_rates`.
- **Root Cause**: There is a documentation/implementation drift. `simulation/dtos/api.py:L146` contains a comment claiming this was refactored to a `TypedDict`, but the actual implementation in `modules/system/api.py` remains a strict `@dataclass`.

### 2. MarketSnapshotDTO: Missing Required 'market_data'
- **Status**: ⚠️ Breaking Positional Change
- **Evidence**: `modules/system/api.py:L64-74`
- **Findings**: The `MarketSnapshotDTO.__init__` requires three positional arguments: `tick`, `market_signals`, and `market_data`.
- **Issue**: Multiple integration tests (`test_agent_decision.py`, `test_stress_scenarios.py`, `test_decision_unit.py`) are failing because they provide only two arguments, omitting the mandatory `market_data` dictionary.

### 3. MarketSignalDTO: Outdated Call Sites
- **Status**: ⚠️ Field Evolution Regression
- **Evidence**: `modules/system/api.py:L22-35`
- **Findings**: `MarketSignalDTO` has been expanded with three new mandatory fields: `total_bid_quantity`, `total_ask_quantity`, and `is_frozen`.
- **Evidence of Desync**:
    - **2 Missing Args**: `test_public_manager_integration.py` and `test_public_manager.py` are failing to provide `total_bid_quantity` and `total_ask_quantity`.
    - **3 Missing Args**: `test_household_ai.py` is failing to provide all three new fields, indicating it is trailing the schema by several versions.

## Risk Assessment
- **Integration Stability**: The lack of default values for new fields in `api.py` has effectively disabled the public manager and household AI testing pipelines.
- **Architectural Guardrail Violation**: The discrepancy between the "Universal Data Hub" vision and the actual code suggests a violation of the **DTO Purity** mandate, as the types are not being consistently updated across boundaries.

## Conclusion
The system is currently experiencing a regression due to uncoordinated API hardening. 

**Recommended Actions:**
1. **Restore Compatibility**: Add default values to `total_bid_quantity`, `total_ask_quantity`, and `is_frozen` in `MarketSignalDTO` to prevent breakage of legacy tests.
2. **Synchronize Context**: Update `MarketContextDTO` in `modules/system/api.py` to support `exchange_rates` or remove the field from callers.
3. **Audit Callers**: Update `MarketSnapshotDTO` call sites to include a `market_data` dictionary (even if empty) to satisfy the positional contract.