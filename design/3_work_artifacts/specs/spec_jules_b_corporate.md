# Spec: Workstream B - Corporate & Decision Unit Tests

## Objective
Fix broken unit tests in corporate and decision modules caused by DTO structure changes.

## Scope
1.  **tests/unit/corporate/**:
    *   Update `conftest.py` firm_dto creation. Remove 'assets' and use `FinancialStateDTO` where necessary.
2.  **tests/unit/decisions/**:
    *   Update `test_animal_spirits_phase2.py`, `test_household_engine_refactor.py`.
    *   Inject missing `_econ_state` and `_bio_state` Mocks into Household MagicMocks.

## Validation
- `pytest tests/unit/corporate/`
- `pytest tests/unit/decisions/`
