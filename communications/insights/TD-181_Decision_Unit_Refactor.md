# Technical Debt Resolution: TD-181 Decision Unit Refactor

- **Date**: 2026-05-21
- **Author**: Jules (AI Agent)
- **Status**: Completed
- **Related Issues**: TD-181, TD-182

## 1. Overview
This refactoring enforces a strict DTO-only data flow between the `Household` agent and its `DecisionUnit`. Previously, `DecisionUnit` received live objects (`markets` dictionary, `EconContextDTO` with live references), violating encapsulation and creating a "God Object" dependency.

## 2. Changes Implemented
- **DTOs Introduced**:
    - `HousingMarketUnitDTO`, `HousingMarketSnapshotDTO`
    - `LoanMarketSnapshotDTO`, `LaborMarketSnapshotDTO`
    - `MarketSnapshotDTO`
    - `OrchestrationContextDTO`
- **Interface Updates**:
    - `IDecisionUnit.orchestrate_economic_decisions` now accepts `OrchestrationContextDTO`.
    - Removed `IDecisionUnit.make_decision` wrapper method.
- **Refactoring**:
    - `DecisionUnit` is now purely stateless and operates only on DTOs.
    - `Household.make_decision` acts as an Anti-Corruption Layer (ACL), constructing DTOs from live engine objects before invoking the `DecisionUnit`.

## 3. Remaining Technical Debt
- **Agent Registry**: The `agent_registry` is still passed as a raw dictionary or via `DecisionContext`. A similar "Snapshot DTO" approach should be applied to `agent_registry` in a future task (as noted in spec TD-181 Risk 2).
- **Test Coverage**: While `DecisionUnit` is now unit-tested with DTOs, integration tests for `Household`'s DTO construction logic should be expanded to cover edge cases (e.g. missing markets, malformed orders).

## 4. Verification
- `tests/unit/modules/household/test_decision_unit.py` passes, verifying the DTO-driven logic for housing decisions and shadow wage updates.
