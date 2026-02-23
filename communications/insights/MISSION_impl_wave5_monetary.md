# Insight Report: Wave 5 Monetary Strategy Pattern
**Mission Key:** MISSION_impl_wave5_monetary
**Date:** 2026-02-23
**Author:** Jules (Software Engineer)

## 1. Architectural Insights & Technical Debt

### 1.1. Single Source of Truth (SSoT) Alignment
- **Decision**: `EconomicIndicatorTracker` was updated to track `monetary_base` (M0) and expose `gdp_history` and `cpi_history`. This ensures the `CentralBank` has access to the same SSoT as other agents via `MacroEconomicSnapshotDTO`.
- **Reasoning**: The McCallum Rule requires M0 (Base Money) targeting. Previously, only M2 (Money Supply) was tracked. By exposing M0, we enable precise Base Money targeting.

### 1.2. Protocol Purity & Strategy Pattern
- **Decision**: Refactored `CentralBank` to use `IMonetaryStrategy` protocol. The `MonetaryEngine` was deprecated and replaced by dynamic strategy injection (`TaylorRuleStrategy`, `FriedmanKPercentStrategy`, `McCallumRuleStrategy`).
- **Benefit**: This allows the simulation to switch monetary regimes (Keynesian vs. Monetarist) at runtime or via configuration without code changes.

### 1.3. OMO Execution Gap Resolution
- **Resolution**: `CentralBank` now implements `execute_open_market_operation` which generates real `Order` objects for the `security_market`.
- **Dependency**: The `CentralBank` now requires a reference to `BondMarket`. This dependency is injected via `set_bond_market` in `SimulationInitializer` to handle the circular dependency (Bank created before Market).

## 2. Regression Analysis
- **Taylor Rule**: The new `TaylorRuleStrategy` replicates the logic of the legacy `MonetaryEngine`.
    - **Regression**: The legacy implementation used a custom `output_gap` calculation derived from Potential GDP.
    - **Mitigation**: The `MacroEconomicSnapshotDTO` includes `output_gap` which `CentralBank` populates using its internal `potential_gdp` tracking (preserved from legacy). This ensures identical behavior for the default strategy.
    - **Test Evidence**: `tests/modules/finance/monetary/test_strategies.py::test_taylor_rule` passes with expected values.

- **Economic Tracker**: `EconomicIndicatorTracker.track()` signature was updated.
    - **Compatibility**: The new `monetary_base` argument is optional (defaults to 0.0) to preserve compatibility with existing tests that call `track()` manually.
    - **Update**: `TickOrchestrator` was updated to pass the real `monetary_base` (from `WorldState.calculate_base_money()`).

## 3. Test Evidence

### 3.1. New Strategy Tests
```
tests/modules/finance/monetary/test_strategies.py::test_taylor_rule PASSED [ 12%]
tests/modules/finance/monetary/test_strategies.py::test_taylor_rule_no_explicit_output_gap PASSED [ 25%]
tests/modules/finance/monetary/test_strategies.py::test_friedman_rule PASSED [ 37%]
tests/modules/finance/monetary/test_strategies.py::test_mccallum_rule PASSED [ 50%]
```

### 3.2. Central Bank Refactor Tests
```
tests/simulation/agents/test_central_bank_refactor.py::test_central_bank_initialization PASSED [ 62%]
tests/simulation/agents/test_central_bank_refactor.py::test_central_bank_step_delegates_to_strategy PASSED [ 75%]
tests/simulation/agents/test_central_bank_refactor.py::test_central_bank_omo_execution PASSED [ 87%]
tests/simulation/agents/test_central_bank_refactor.py::test_central_bank_snapshot_construction PASSED [100%]
```

### 3.3. Full Suite Regression Check
Ran `pytest tests/` (1029 tests).
**Result:** 1029 passed, 11 skipped. 100% Pass Rate.
