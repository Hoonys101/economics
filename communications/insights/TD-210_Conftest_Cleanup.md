# Insight: Conftest Cleanup (TD-210)

## Context
The `tests/conftest.py` file contained imports for `simulation.agents.central_bank.CentralBank` and `simulation.bank.Bank`. These imports were used solely for `spec` arguments in `unittest.mock.Mock`.

## Problem
`CentralBank` imports `numpy`, a heavy library. Importing it in `conftest.py` causes `numpy` to be loaded during test collection and initialization, even for tests that do not require it. This slows down the test suite startup time.

## Solution
- Removed `CentralBank` and `Bank` imports from `tests/conftest.py`.
- Replaced `Mock(spec=CentralBank)` with `Mock()`.
- Replaced `Mock(spec=Bank)` with `Mock()`.
- Preserved the necessary attribute configurations on the mocks (`get_base_rate`, `_assets`).

## Impact
- **Test Initialization Speed**: Faster startup time for pytest, especially for non-simulation tests.
- **Dependency Isolation**: Reduced coupling between `conftest.py` and simulation agents.
- **Maintenance**: Less risk of circular imports or dependency issues in the test runner configuration.

## Verification
- Verified that `conftest.py` no longer imports `CentralBank` or `Bank`.
- Verified that mocks are still configured correctly.
- Tests depending on these fixtures should still pass as the mocks provide the necessary interface (duck typing).
