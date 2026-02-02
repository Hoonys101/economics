# TD-122-B: Unit Test Repair (Household Refactor Fallout)

## Context
The "Stage B" refactor of the `Household` class (removing property delegates and enforcing DTO usage) has introduced widespread regressions in the unit test suite. Specifically, tests that utilize `MagicMock(spec=Household)` fail because the mock does not automatically create the nested `_econ_state`, `_bio_state`, and `_social_state` DTOs, leading to `AttributeError` when the refactored code attempts to access them (e.g., `h._econ_state.assets`).

## Scope
Approximately 128 unit tests are failing. The critical system integration paths (`Settlement`, `Housing`, `Inheritance`, `Government`) have been manually verified and fixed, but the long tail of component-level unit tests requires mechanical updates.

## Affected Areas
- `tests/unit/components/`
- `tests/unit/decisions/`
- `tests/unit/systems/` (Non-critical systems)
- `tests/unit/test_*.py` (Root unit tests)

## Action Plan
1.  **Refactor Test Fixtures**: Update `tests/conftest.py` or individual test `setUp` methods to use a helper factory that properly populates the `Household` mock with its state DTOs.
    ```python
    def create_mock_household(id, assets=0):
        h = MagicMock(spec=Household)
        h.id = id
        h._econ_state = MagicMock()
        h._econ_state.assets = assets
        # ... initialize other states
        return h
    ```
2.  **Iterate & Fix**: Systematically work through the `test_failures_household_refactor.log` to apply this pattern.
3.  **Deprecate Legacy Logic**: Remove tests that cover deprecated logic (e.g., legacy `collect_tax` adapters) if they are no longer relevant.

## Priority
**Medium**. The simulation core is functional, but the broken test suite hinders future refactoring confidence.
