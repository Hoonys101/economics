# STABILIZE-SYS-V2: System Unit Test Repair

## Background
The following property bridges were already added to `Household` and `Firm`:
- `assets`, `inventory`, `is_active`, `age`, `employer_id`, `skills`, `portfolio`, etc.

However, system unit tests (`tests/unit/systems/`) still have 18-20 failures. The failures are due to:
1. **Constructor Signature Mismatches**: `CommerceSystem` and `EventSystem` now have different __init__ signatures than the fixtures expect.
2. **Mock Object Incompatibility**: Tests use `MagicMock` objects that lack internal state DTOs (`_bio_state`, `_econ_state`). Systems now access public properties which work on real agents but fail on mocks.
3. **Direct State Access**: Some systems (e.g., `social_system.py`, `commerce_system.py`) still use `._bio_state` directly instead of public properties.

## Task
1. Analyze the test failure log at `c:\coding\economics\logs\systems_test_failures_v3.log`.
2. For each failure, determine if the fix should be in the **test fixture** (Mock setup) or in the **system code** (switch to public properties).
3. Prioritize **test stability**: Tests should pass against the REAL codebase. Update Mock fixtures to properly simulate agent structure.

## Files to Review
- `tests/unit/systems/test_commerce_system.py`
- `tests/unit/systems/test_commerce_system_logging.py`
- `tests/unit/systems/test_event_system.py`
- `tests/unit/systems/test_social_system.py`
- `tests/unit/systems/test_firm_management_leak.py`
- `tests/unit/systems/test_firm_management_refactor.py`
- `tests/unit/systems/test_ministry_of_education.py`
- `tests/unit/systems/test_demographic_manager_newborn.py`
- `tests/unit/systems/handlers/test_housing_handler.py`
- `tests/unit/systems/test_registry_housing.py`
- `simulation/systems/commerce_system.py`
- `simulation/systems/social_system.py`

## Acceptance Criteria
- `pytest tests/unit/systems/` passes with 0 failures and 0 errors.
- No direct `_bio_state` or `_econ_state` access in system code (use public properties).
- All Mock fixtures correctly simulate agent state structure.
