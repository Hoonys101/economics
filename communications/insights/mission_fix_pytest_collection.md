# Technical Insight Report: Pytest Collection & Structural Fixes

## 1. Problem Phenomenon
The entire test suite (`pytest --collect-only`) was failing to collect tests due to multiple `ImportError` and `ModuleNotFoundError` exceptions. Specific symptoms included:
- `ModuleNotFoundError: No module named 'simulation.components.finance_department'`: Legacy component reference in integration tests.
- `ImportError: cannot import name 'GovernmentStateDTO' from 'simulation.dtos'`: Outdated DTO reference in scenario tests.
- `PytestCollectionWarning`: A DTO class named `TestConfigDTO` was being collected as a test class.
- Missing dependencies: `numpy`, `joblib`, `fastapi`, `PyYAML`, etc. were missing from the environment, causing cascading import failures.

## 2. Root Cause Analysis
- **Legacy Code Debt**: `FinanceDepartment` was removed in a previous refactor (Firm Orchestrator-Engine pattern) but `test_wo167_grace_protocol.py` was not updated to use `FinanceEngine` and `FinanceState`.
- **DTO Refactoring Drift**: `GovernmentStateDTO` was likely renamed or split, and `test_leviathan_emergence.py` was using an old name/import path. The correct DTO for the test's purpose (sensory data) is `GovernmentSensoryDTO`.
- **Naming Convention Violation**: `TestConfigDTO` in `test_impl.py` started with `Test`, triggering pytest's discovery mechanism unintentionally.
- **Environment Drift**: The local environment lacked packages specified in `requirements.txt`.

## 3. Solution Implementation Details
1.  **Dependency Management**: Installed missing dependencies via `pip install -r requirements.txt`.
2.  **Integration Test Fix (`test_wo167_grace_protocol.py`)**:
    - Replaced `FinanceDepartment` with `FinanceState`.
    - Updated mock setup to attach `finance_state`, `finance_engine`, and `wallet` to the mock Firm.
    - Updated assertions to check `firm.finance_state.is_distressed` instead of `firm.finance.is_distressed`.
3.  **Scenario Test Fix (`test_leviathan_emergence.py`)**:
    - Replaced `GovernmentStateDTO` with `GovernmentSensoryDTO` imported from `simulation.dtos.api`.
    - Verified that fields match the `GovernmentSensoryDTO` definition.
4.  **Unit Test Fix (`test_impl.py`)**:
    - Renamed `TestConfigDTO` to `ConfigDTOTest` to prevent accidental test collection.

## 4. Lessons Learned & Technical Debt
- **Mock Purity**: Tests relying on `MagicMock` for complex agents (like Firm/Household) are fragile to refactors. The mocks should be updated immediately when core components change. Consider using factories that return properly structured mocks or real objects with mocked dependencies.
- **DTO Stability**: Renaming DTOs without checking usage in tests leads to "rot". `GovernmentSensoryDTO` vs `GovernmentStateDTO` confusion suggests a need for stricter naming or deprecation aliases during transition.
- **Test Discovery**: Naming helper classes with `Test` prefix is a common pitfall. Strict adherence to naming conventions (e.g., `*DTO`, `Mock*`) helps avoid this.
- **Environment Verification**: CI/CD pipelines usually catch missing dependencies, but local dev setups can drift. Always verify `pip list` matches `requirements.txt`.
