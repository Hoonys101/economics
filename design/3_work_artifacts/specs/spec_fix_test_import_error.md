
# Mission Guide: Fix Cockpit Integration Test Import Error

## 1. Objectives
- Resolve `ImportError: cannot import name 'MarketContextDTO' from 'modules.system.api'` encountered during `test_cockpit_integration.py`.
- Ensure `modules/finance/api.py` correctly imports `MarketContextDTO`.
- Verify that `tests/integration/test_cockpit_integration.py` passes successfully.

## 2. Reference Context (MUST READ)
- **Error Log**: `ImportError` in `modules/finance/api.py` trying to import `MarketContextDTO` from `modules.system.api`.
- **Related Files**:
    - `modules/system/api.py`: `MarketContextDTO` was recently added here.
    - `modules/finance/api.py`: The file failing to import.
    - `tests/integration/test_cockpit_integration.py`: The test triggering the error.

## 3. Implementation Roadmap
### Phase 1: Verify and Fix Import
1.  Check `modules/finance/api.py`. It likely has `from modules.system.api import ... MarketContextDTO ...`.
2.  Ensure `modules/system/api.py` actually exports `MarketContextDTO` (it was added, but verify cache/paths).
3.  If `MarketContextDTO` is confirmed in `system/api.py`, the issue might be a circular import triggered by `finance/api.py` importing `system/api.py`.
    - Check if `system/api.py` imports anything from `finance/api.py` (it shouldn't, based on architecture, but double check).

### Phase 2: Run Tests
1.  Run `pytest tests/integration/test_cockpit_integration.py`.
2.  If successful, the mission is complete.
3.  If other import errors arise (e.g. circular dependency in `conftest.py`), resolve them by moving imports into functions or using `TYPE_CHECKING` blocks.

## 4. Verification
- Run: `pytest tests/integration/test_cockpit_integration.py`
- Expectation: All tests in this file pass.
