# Implementation Plan - TD-072: Test Framework Migration

## Goal Description
Migrate legacy `unittest.TestCase` based tests to the standard `pytest` framework to ensure consistency, reduce boilerplate, and enable advanced fixture usage. This is a "Yellow" Technical Debt item (TD-072).

## User Review Required
> [!NOTE]
> This is a refactoring task. Behavior should remain identical.

## Proposed Changes

### Tests
#### [MODIFY] [test_government.py](file:///c:/coding/economics/tests/agents/test_government.py)
- Remove `unittest.TestCase` inheritance and `unittest.main()` block.
- Convert `setUp` to `pytest.fixture` (e.g., `government`, `mock_tax_agency`).
- Replace `self.assertX` with standard python `assert`.
- Use `pytest-mock` via the `mocker` fixture instead of `patch` decorators where appropriate (or keep patch if cleaner).

#### [MODIFY] [verify_vanity_society.py](file:///c:/coding/economics/tests/verify_vanity_society.py)
- Remove `unittest.TestCase` inheritance and `unittest.main()` block.
- Convert `setUp` to a `vanity_config` fixture.
- Replace `self.assertEqual`, `self.assertTrue`, `self.assertIsNone` with `assert`.

## Verification Plan

### Automated Tests
Run the specific tests to ensure they pass:
```bash
pytest tests/agents/test_government.py tests/verify_vanity_society.py -v
```
