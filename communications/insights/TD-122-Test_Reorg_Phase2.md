# Insight: TD-122 Test Reorganization Phase 2

## P: Phenomenon
During the reorganization of tests into `tests/unit`, `tests/integration`, and `tests/system`, several existing tests in legacy directories (`tests/stress`, `tests/market`, etc.) were found to be broken due to API evolution and code drift. Specifically:
1.  `tests/unit/systems/handlers/test_housing_handler.py` failed to import its target module (path did not exist).
2.  `tests/stress/test_stress_scenarios.py` failed with `TypeError` due to `DecisionOutputDTO` not being iterable (unpacking error), `MarketSnapshotDTO` signature mismatch, and missing attributes on Mocks (`perceived_prices`, `avg_wage` on labor snapshot).
3.  `tests/market/test_housing_transaction_handler.py` failed due to Mock object comparison logic errors (`MagicMock` vs string).

## C: Cause
The "flat" or fragmented test directory structure allowed these tests to be ignored or excluded from the main test loop (possibly due to not being discovered or just neglected). As the codebase evolved (introducing `DecisionInputDTO`, `MarketSnapshotDTO`, refactoring `Household.make_decision`), these peripheral tests were not updated.

## S: Solution
1.  **Migration**: Moved tests to their appropriate canonical locations (`tests/unit/markets`, `tests/integration/scenarios`, etc.).
2.  **Repair**:
    -   Updated `test_stress_scenarios.py` to use `DecisionInputDTO` and access `DecisionOutputDTO.orders` attribute.
    -   Updated `MarketSnapshotDTO` usage to match current definition.
    -   Fixed Mock configurations in `test_housing_transaction_handler.py` and `test_stress_scenarios.py`.
3.  **Pruning**: Deleted the permanently broken and redundant `tests/unit/systems/handlers/test_housing_handler.py`.

## L: Lesson Learned
**"Out of sight, out of mind" applies to tests.**
Tests scattered in non-standard directories are prone to bit-rot. Centralizing them into a standard `tests/{unit,integration,system}` hierarchy ensures they are discoverable and maintained alongside core changes. The reorganization process itself acts as an audit, revealing hidden technical debt.
