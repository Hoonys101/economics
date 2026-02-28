# MISSION: Track D - Fix Remaining Test Failures
# Role: Jules

## Objective
Fix the remaining test failures related to `DeathContextAdapter` and `test_omo_system.py`.

## Failures
1. `AttributeError: 'DeathContextAdapter' object has no attribute 'stock_market'`
   - Arises in `simulation\systems\inheritance_manager.py:74` and fails `tests/integration/scenarios/test_scenario_runner.py`.
2. `assert 500 == (500 + 100)`
   - Arises in `tests\integration\test_omo_system.py:201` (`test_process_omo_purchase_transaction`).

## Specific Tasks
1. Investigate and fix the `DeathContextAdapter` (or `simulation/systems/inheritance_manager.py`) so that it provides or safely ignores the `stock_market` dependency. In Phase 20+, a stock market is not guaranteed to exist in all test contexts (`test_scenario_runner.py`). Check where `stock_market` is accessed and handle it securely.
2. Investigate and fix the failed assertion in `tests\integration\test_omo_system.py:201`. Ensure that OMO purchases correctly increase the target agent's assets and that the tests are asserting the correct values. It may be a simple logic bug in the test or the mock setup.

## Success Criteria
- `pytest tests/integration/test_omo_system.py` passes.
- `pytest tests/integration/scenarios/test_scenario_runner.py` passes.
- No `AttributeError` for `stock_market`.
