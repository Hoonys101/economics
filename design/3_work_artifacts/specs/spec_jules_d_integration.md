# Spec: Workstream D - Integration & System Scenarios

## Objective
Restore high-level scenario and integration tests.

## Scope
1.  **tests/integration/**:
    *   `test_m2_integrity.py`: Adjust assertions to match new DTO sync timing.
    *   `test_government_ai_logic.py`, `test_fiscal_policy.py`.
2.  **tests/system/**:
    *   `test_phase29_depression.py`: Update crisis monitor log expectations.
    *   `test_engine.py`: Fix SimulationState DTO access.

## Success Criteria
- Global M2 integrity remains 100% (No leaks).
- High-level scenario tests pass with the new DTO-based agents.
